# app/engine/vision.py
"""
Vision Engine — EfficientNetB3 inference implementation.

Implements VisionEngineProtocol. All PyTorch work runs synchronously
inside a thread pool via asyncio.to_thread() to avoid blocking the
async event loop (Rule 03 — AGENTS.md; production constraint).

Architecture (SRP breakdown):
  _decode_image_bytes()   → bytes → PIL.Image
  _build_transform()      → torchvision transforms pipeline
  _run_inference()        → PIL.Image + model → VisionPrediction
  classify_image()        → public async entry point (dispatches to thread)
"""

from __future__ import annotations

import asyncio
import io
import logging
from typing import TYPE_CHECKING

import torch
import torch.nn as nn
from PIL import Image, UnidentifiedImageError
from torchvision import transforms

from app.config import (
    IMAGE_INPUT_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
)
from app.exceptions import InferenceError, InvalidImageError, ModelNotLoadedError
from app.schemas import PredictionItem, VisionPrediction

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ── Transform Pipeline (built once; immutable after construction) ──────────────

_INFERENCE_TRANSFORM = transforms.Compose(
    [
        transforms.Resize(IMAGE_INPUT_SIZE),
        transforms.CenterCrop(IMAGE_INPUT_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=list(IMAGENET_MEAN), std=list(IMAGENET_STD)),
    ]
)


# ── Private Helpers ───────────────────────────────────────────────────────────


def _decode_image_bytes(raw_bytes: bytes) -> Image.Image:
    """
    Decode raw bytes into a PIL RGB image.

    Args:
        raw_bytes: Binary content read from the uploaded file.

    Returns:
        A PIL Image converted to RGB colour space.

    Raises:
        InvalidImageError: If the bytes cannot be decoded as a valid image.
    """
    try:
        image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        # Force PIL to fully load the image data to detect corrupt files early.
        image.load()
        return image
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise InvalidImageError(detail=str(exc)) from exc


def _apply_transform(image: Image.Image) -> torch.Tensor:
    """
    Apply the inference transform pipeline to a PIL image, generating multiple
    augmented versions for Test-Time Augmentation (TTA).

    Args:
        image: A decoded PIL.Image.Image in RGB mode.

    Returns:
        A normalised float32 tensor of shape (5, 3, 300, 300) containing TTA crops.
    """
    base_tensor: torch.Tensor = _INFERENCE_TRANSFORM(image)
    
    # Generate TTA variations (orientation-invariant for skin lesions)
    tensors = [
        base_tensor,
        torch.flip(base_tensor, dims=[2]), # Horizontal flip
        torch.flip(base_tensor, dims=[1]), # Vertical flip
        torch.rot90(base_tensor, k=1, dims=[1, 2]), # Rotate 90 degrees
        torch.rot90(base_tensor, k=3, dims=[1, 2]), # Rotate 270 degrees
    ]
    
    return torch.stack(tensors)  # (5, 3, H, W)


def _select_inference_device() -> torch.device:
    """
    Return the best available torch.device (CUDA > CPU).

    Returns:
        torch.device set to 'cuda' if available, else 'cpu'.
    """
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _run_forward_pass(
    model: nn.Module,
    input_tensor: torch.Tensor,
    device: torch.device,
    top_k: int = 3,
) -> tuple[list[int], list[float]]:
    """
    Execute the neural network forward pass and calculate softmax probabilities.

    Args:
        model:        The loaded PyTorch model in eval mode.
        input_tensor: The preprocessed image tensor (1, 3, H, W).
        device:       The device to run inference on (CPU/CUDA/MPS).
        top_k:        Number of top predictions to return.

    Returns:
        A tuple of (list of class_indices, list of confidence_scores).

    Raises:
        InferenceError: If the forward pass fails due to OOM or shape mismatch.
    """
    try:
        with torch.no_grad():
            # Process TTA sequentially to prevent Out-Of-Memory (OOM) on 512MB RAM free-tier servers.
            logits_list = []
            for i in range(input_tensor.size(0)):
                single_input = input_tensor[i:i+1].to(device)
                single_logits = model(single_input)
                logits_list.append(single_logits)
            
            logits = torch.cat(logits_list, dim=0) # shape: (5, num_classes)
            
            # Average the logits across all 5 augmented versions to get consensus
            mean_logits = torch.mean(logits, dim=0, keepdim=True) # shape: (1, num_classes)
            
            probabilities = torch.nn.functional.softmax(mean_logits, dim=1)
            
            # Extract top K probabilities and their indices
            top_probs, top_indices = torch.topk(probabilities, k=top_k, dim=1)
            
            scores = top_probs.squeeze(0).tolist()
            indices = top_indices.squeeze(0).tolist()
            return indices, scores
    except Exception as exc:
        raise InferenceError(detail=str(exc)) from exc


def _map_index_to_prediction(
    class_indices: list[int],
    confidence_scores: list[float],
    class_names: list[str],
) -> VisionPrediction:
    """
    Map raw class indices to a VisionPrediction DTO containing PredictionItems.

    Args:
        class_indices:      List of raw argmax indices from the model output.
        confidence_scores:  List of softmax probabilities.
        class_names:        List of string labels extracted from the model checkpoint.

    Returns:
        A fully-populated VisionPrediction schema instance.

    Raises:
        InferenceError: If any class index is out of bounds for the known classes.
    """
    predictions = []
    
    for idx, score in zip(class_indices, confidence_scores):
        if idx < 0 or idx >= len(class_names):
            raise InferenceError(
                detail=(
                    f"Model returned class index {idx} which is out of bounds "
                    f"for {len(class_names)} known classes."
                )
            )
            
        raw_class_name = class_names[idx]
        
        # Format raw dataset names (e.g., 'fitz_acanthosis_nigricans' -> 'Acanthosis Nigricans')
        formatted_class = raw_class_name.replace("fitz_", "").replace("ham_", "").replace("_", " ").title()
        if formatted_class.endswith(" Ssm"):
            formatted_class = formatted_class.replace(" Ssm", " (SSM)")

        predictions.append(
            PredictionItem(
                disease_name=formatted_class,
                confidence=score,
                class_index=idx,
            )
        )

    return VisionPrediction(predictions=predictions)


# ── Synchronous Inference Core (runs in thread pool) ─────────────────────────


def _synchronous_classify(model: nn.Module, class_names: list[str], image_bytes: bytes) -> VisionPrediction:
    """
    Synchronous classification pipeline — intended to run inside a thread pool.

    Orchestrates: decode → transform → forward pass → map to DTO.

    Args:
        model:       The loaded EfficientNetB3 nn.Module in eval mode.
        class_names: List of string labels extracted from the model checkpoint.
        image_bytes: Raw bytes from the uploaded image file.

    Returns:
        VisionPrediction DTO.

    Raises:
        InvalidImageError:  On image decoding failure.
        InferenceError:     On model forward pass failure.
    """
    device = _select_inference_device()
    pil_image = _decode_image_bytes(image_bytes)
    input_tensor = _apply_transform(pil_image)
    class_indices, confidence_scores = _run_forward_pass(model, input_tensor, device)
    prediction = _map_index_to_prediction(class_indices, confidence_scores, class_names)
    
    top_pred = prediction.predictions[0]
    logger.info(
        "Inference complete: top_class=%s, confidence=%.4f",
        top_pred.disease_name,
        top_pred.confidence,
    )
    return prediction


# ── Public Engine Class ───────────────────────────────────────────────────────


class VisionEngine:
    """
    Non-blocking Vision Engine satisfying VisionEngineProtocol.

    Holds a reference to the loaded model from application state.
    All CPU-bound PyTorch work is dispatched to a thread pool so the
    async event loop is never blocked.

    Args:
        model: An EfficientNetB3 nn.Module loaded and in eval() mode.
    """

    def __init__(self, model: nn.Module, class_names: list[str]) -> None:
        self._model = model
        self._class_names = class_names

    async def classify_image(self, image_bytes: bytes) -> VisionPrediction:
        """
        Async entry point for image classification.

        Validates the model is present, then dispatches the synchronous
        inference pipeline to asyncio's default thread pool executor.

        Args:
            image_bytes: Raw bytes from the UploadFile.

        Returns:
            VisionPrediction DTO.

        Raises:
            ModelNotLoadedError: If self._model is None.
            InvalidImageError:   If the bytes are not a decodable image.
            InferenceError:      If the model forward pass fails.
        """
        if self._model is None:
            raise ModelNotLoadedError()

        return await asyncio.to_thread(
            _synchronous_classify,
            self._model,
            self._class_names,
            image_bytes,
        )


# ── Model Loader ──────────────────────────────────────────────────────────────


def load_efficientnet_b3_from_checkpoint(
    checkpoint_path: str,
) -> tuple[nn.Module, list[str]]:
    """
    Load an EfficientNetB3 model and its labels from a .pth checkpoint file.

    Extracts `idx_to_class` dynamically from the checkpoint to determine
    the `num_classes`. Builds the torchvision EfficientNet-B3 architecture,
    replaces the classifier head, loads the state dict, and sets eval mode.

    Args:
        checkpoint_path: Absolute or relative path to the .pth file.

    Returns:
        A tuple of (nn.Module in eval() mode, list of class names).

    Raises:
        FileNotFoundError: If the checkpoint file does not exist.
        RuntimeError:      If the state dict is incompatible or metadata is missing.
    """
    from torchvision.models import efficientnet_b3

    device = _select_inference_device()
    logger.info("Loading EfficientNetB3 checkpoint from '%s' onto %s", checkpoint_path, device)

    # Note: weights_only=False is required to load custom dictionaries (idx_to_class) embedded in the .pth
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

    # Extract labels from checkpoint metadata
    idx_to_class = checkpoint.get("idx_to_class")
    if not idx_to_class or not isinstance(idx_to_class, dict):
        raise RuntimeError("Checkpoint is missing the required 'idx_to_class' dictionary metadata.")

    # Reconstruct the ordered list of labels
    class_names = [idx_to_class[i] for i in range(len(idx_to_class))]
    num_classes = len(class_names)
    logger.info("Dynamically extracted %d class labels from checkpoint.", num_classes)

    model = efficientnet_b3(weights=None)
    in_features: int = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(in_features=in_features, out_features=num_classes),
    )

    state_dict = _extract_state_dict(checkpoint)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    logger.info("Model loaded successfully. Classes=%d, Device=%s", num_classes, device)
    return model, class_names


def _extract_state_dict(checkpoint: object) -> dict:
    """
    Normalise checkpoint format to a plain state_dict dictionary.

    Handles both bare state dicts and wrapped checkpoint dicts that
    store the weights under a 'state_dict' or 'model_state_dict' key.

    Args:
        checkpoint: The raw object returned by torch.load().

    Returns:
        A dict suitable for model.load_state_dict().

    Raises:
        RuntimeError: If the checkpoint format is unrecognised.
    """
    if isinstance(checkpoint, dict):
        for key in ("state_dict", "model_state_dict"):
            if key in checkpoint:
                return checkpoint[key]
        return checkpoint  # Assume it is already a bare state dict
    raise RuntimeError(
        f"Unrecognised checkpoint format: {type(checkpoint)}. "
        "Expected a dict containing model weights."
    )
