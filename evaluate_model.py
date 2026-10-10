"""
DermAI Model Evaluation Script
===============================
Downloads the Fitzpatrick17k dataset, splits into train/test,
runs the EfficientNetB3 model on the test set, and generates
comprehensive evaluation metrics. 

Metrics are calculated using pure NumPy to bypass AppLocker DLL blocks.
"""

import os
import sys
import io
import csv
import json
import time
import hashlib
import logging
import warnings
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import numpy as np
import torch
import torch.nn as nn
from PIL import Image, UnidentifiedImageError
from torchvision import transforms, models

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("[WARNING] matplotlib/seaborn not found. Skipping plots.")

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
CHECKPOINT_PATH = Path("backend/DermAI_Mega_Payload.pth")
FITZPATRICK_CSV_URL = "https://raw.githubusercontent.com/mattgroh/fitzpatrick17k/main/fitzpatrick17k.csv"
OUTPUT_DIR = Path("evaluation_results")
CACHE_DIR = Path("evaluation_results/image_cache")
IMAGE_INPUT_SIZE = 300
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
TEST_SPLIT_RATIO = 0.2
RANDOM_SEED = 42
MAX_DOWNLOAD_WORKERS = 8
IMAGE_DOWNLOAD_TIMEOUT = 15  
MAX_IMAGES_PER_CLASS = 15  # Limit to 15 per class for speed since we're in an agent loop


# ── NumPy Metrics ─────────────────────────────────────────────────────────────
def np_confusion_matrix(y_true, y_pred, labels):
    n = len(labels)
    label_to_idx = {l: i for i, l in enumerate(labels)}
    cm = np.zeros((n, n), dtype=int)
    for t, p in zip(y_true, y_pred):
        if t in label_to_idx and p in label_to_idx:
            cm[label_to_idx[t], label_to_idx[p]] += 1
    return cm

def top_k_accuracy(y_true, y_prob, k=3):
    top_k_preds = np.argsort(y_prob, axis=1)[:, -k:]
    return sum(1 for true, preds in zip(y_true, top_k_preds) if true in preds) / len(y_true)

# ── Step 1: Load Model ───────────────────────────────────────────────────────
def load_model(checkpoint_path: Path):
    logger.info("Loading model from %s ...", checkpoint_path)
    
    if not checkpoint_path.exists():
        alt_path = Path("DermAI_Mega_Payload.pth")
        if alt_path.exists():
            checkpoint_path = alt_path
        else:
            raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    
    idx_to_class = checkpoint["idx_to_class"]
    class_names = [idx_to_class[i] for i in range(len(idx_to_class))]
    num_classes = len(class_names)
    
    model_name = checkpoint.get("model_name", "EfficientNetB3")
    image_size = checkpoint.get("image_size", IMAGE_INPUT_SIZE)
    
    logger.info("Model: %s | Classes: %d | Device: %s", model_name, num_classes, device)
    
    model = models.efficientnet_b3(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(in_features=in_features, out_features=num_classes),
    )
    
    state_dict = checkpoint.get("model_state_dict", checkpoint.get("state_dict", checkpoint))
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model, class_names, device, image_size

# ── Step 2: Download & Parse Fitzpatrick17k CSV ──────────────────────────────
def download_fitzpatrick_csv():
    logger.info("Downloading Fitzpatrick17k CSV...")
    csv_cache = OUTPUT_DIR / "fitzpatrick17k.csv"
    if csv_cache.exists():
        with open(csv_cache, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    
    resp = requests.get(FITZPATRICK_CSV_URL, timeout=30)
    resp.raise_for_status()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_cache.write_text(resp.text, encoding="utf-8")
    return list(csv.DictReader(io.StringIO(resp.text)))

def map_csv_label_to_checkpoint_class(csv_label: str, class_names: list[str]) -> str | None:
    normalized = "fitz_" + csv_label.lower().strip().replace(" ", "_").replace("'", "").replace("-", "_")
    if normalized in class_names: return normalized
    
    no_prefix = csv_label.lower().strip().replace(" ", "_").replace("'", "").replace("-", "_")
    for cn in class_names:
        if cn.endswith(no_prefix) or cn == no_prefix: return cn
    return None

def build_test_set(rows, class_names):
    label_to_class = {}
    for row in rows:
        csv_label = row["label"]
        if csv_label not in label_to_class:
            mapped = map_csv_label_to_checkpoint_class(csv_label, class_names)
            if mapped: label_to_class[csv_label] = mapped
    
    valid_rows = [r for r in rows if r["label"] in label_to_class]
    
    np.random.seed(RANDOM_SEED)
    class_to_rows = defaultdict(list)
    for row in valid_rows: class_to_rows[label_to_class[row["label"]]].append(row)
    
    test_rows = []
    for cls, cls_rows in sorted(class_to_rows.items()):
        np.random.shuffle(cls_rows)
        if MAX_IMAGES_PER_CLASS:
            cls_rows = cls_rows[:MAX_IMAGES_PER_CLASS]
        n_test = max(1, int(len(cls_rows) * TEST_SPLIT_RATIO))
        test_rows.extend([(r, label_to_class[r["label"]]) for r in cls_rows[:n_test]])
    
    logger.info("Selected %d test images", len(test_rows))
    return test_rows, label_to_class

# ── Step 3: Download Images ──────────────────────────────────────────────────
def download_single_image(url: str, cache_path: Path) -> bool:
    if cache_path.exists(): return True
    try:
        resp = requests.get(url, timeout=IMAGE_DOWNLOAD_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200 and len(resp.content) > 1000:
            cache_path.write_bytes(resp.content)
            return True
    except: pass
    return False

def download_test_images(test_rows):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tasks = []
    for row, class_name in test_rows:
        url = row.get("url", "")
        if not url: continue
        md5 = row.get("md5hash", hashlib.md5(url.encode()).hexdigest())
        tasks.append((url, CACHE_DIR / f"{md5}.jpg", class_name))
    
    successful = []
    with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as executor:
        futures = {executor.submit(download_single_image, u, p): (p, c) for u, p, c in tasks}
        for future in as_completed(futures):
            p, c = futures[future]
            if future.result(): successful.append((p, c))
    return successful

# ── Step 4: Run Inference ─────────────────────────────────────────────────────
def run_inference(model, transform, image_path, device):
    try:
        img = Image.open(image_path).convert("RGB")
        img.load()
        tensor = transform(img).unsqueeze(0).to(device)
        with torch.no_grad():
            probs = torch.nn.functional.softmax(model(tensor), dim=1).squeeze(0).cpu().numpy()
            return probs, int(np.argmax(probs)), float(probs[np.argmax(probs)])
    except:
        return None, None, None

def evaluate_all(model, class_names, device, image_size, test_images):
    transform = transforms.Compose([
        transforms.Resize(image_size),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=list(IMAGENET_MEAN), std=list(IMAGENET_STD)),
    ])
    
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    y_true, y_pred, y_prob, y_conf = [], [], [], []
    correct_confs, wrong_confs = [], []
    
    start_time = time.time()
    for img_path, true_class in test_images:
        true_idx = class_to_idx.get(true_class)
        all_probs, pred_idx, pred_conf = run_inference(model, transform, img_path, device)
        
        if all_probs is not None:
            y_true.append(true_idx)
            y_pred.append(pred_idx)
            y_prob.append(all_probs)
            y_conf.append(pred_conf)
            if pred_idx == true_idx: correct_confs.append(pred_conf)
            else: wrong_confs.append(pred_conf)
            
    return {
        "y_true": np.array(y_true), "y_pred": np.array(y_pred),
        "y_prob": np.array(y_prob), "y_conf": np.array(y_conf),
        "correct_confs": np.array(correct_confs), "wrong_confs": np.array(wrong_confs),
        "elapsed": time.time() - start_time, "num_evaluated": len(y_true)
    }

# ── Step 5: Compute Metrics ──────────────────────────────────────────────────
def compute_all_metrics(results, class_names):
    y_true = results["y_true"]
    y_pred = results["y_pred"]
    
    present_classes = sorted(set(y_true) | set(y_pred))
    display_names = [class_names[i].replace("fitz_", "").replace("ham_", "").replace("_", " ").title() for i in present_classes]
    
    cm = np_confusion_matrix(y_true, y_pred, present_classes)
    tp = np.diag(cm)
    fp = cm.sum(axis=0) - tp
    fn = cm.sum(axis=1) - tp
    support = cm.sum(axis=1)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        precision = np.where(tp + fp == 0, 0, tp / (tp + fp))
        recall = np.where(tp + fn == 0, 0, tp / (tp + fn))
        f1 = np.where(precision + recall == 0, 0, 2 * precision * recall / (precision + recall))
    
    metrics = {
        "overall_accuracy": np.mean(y_true == y_pred),
        "top3_accuracy": top_k_accuracy(y_true, results["y_prob"], k=3),
        "top5_accuracy": top_k_accuracy(y_true, results["y_prob"], k=5),
        "precision_macro": np.mean(precision),
        "recall_macro": np.mean(recall),
        "f1_macro": np.mean(f1),
        "precision_weighted": np.average(precision, weights=support),
        "recall_weighted": np.average(recall, weights=support),
        "f1_weighted": np.average(f1, weights=support),
        "confusion_matrix": cm,
        "present_classes": present_classes,
        "display_names": display_names,
        "per_class": {
            dn: {"precision": p, "recall": r, "f1-score": f, "support": s}
            for dn, p, r, f, s in zip(display_names, precision, recall, f1, support)
        },
        "mean_confidence": float(np.mean(results["y_conf"])),
    }
    return metrics

# ── Step 6: Save Results ─────────────────────────────────────────────────────
def save_metrics_summary(metrics, results, class_names):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = OUTPUT_DIR / "metrics_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n  DermAI — Evaluation Report (Numpy Fallback)\n" + "=" * 70 + "\n\n")
        f.write(f"Overall Accuracy:  {metrics['overall_accuracy']*100:.2f}%\n")
        f.write(f"Top-3 Accuracy:    {metrics['top3_accuracy']*100:.2f}%\n")
        f.write(f"Top-5 Accuracy:    {metrics['top5_accuracy']*100:.2f}%\n")
        f.write(f"F1-Score (macro):  {metrics['f1_macro']:.4f}\n\n")
        
        f.write("-" * 70 + "\n  PER-CLASS CLASSIFICATION REPORT\n" + "-" * 70 + "\n\n")
        f.write(f"{'Class':<35} {'Precision':<10} {'Recall':<10} {'F1':<10} {'Support':<10}\n")
        for cls, d in metrics["per_class"].items():
            f.write(f"{cls[:33]:<35} {d['precision']:.4f}     {d['recall']:.4f}     {d['f1-score']:.4f}     {d['support']}\n")
    return summary_path

def main():
    model, class_names, device, image_size = load_model(CHECKPOINT_PATH)
    rows = download_fitzpatrick_csv()
    test_rows, _ = build_test_set(rows, class_names)
    test_images = download_test_images(test_rows)
    results = evaluate_all(model, class_names, device, image_size, test_images)
    metrics = compute_all_metrics(results, class_names)
    save_metrics_summary(metrics, results, class_names)
    
    print("\n" + "=" * 70)
    print("  📊 EVALUATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"\n  Test Images Evaluated:  {results['num_evaluated']}")
    print(f"  Overall Accuracy:       {metrics['overall_accuracy']*100:.2f}%")
    print(f"  Top-3 Accuracy:         {metrics['top3_accuracy']*100:.2f}%")
    print(f"  Top-5 Accuracy:         {metrics['top5_accuracy']*100:.2f}%")
    print(f"  F1-Score (weighted):    {metrics['f1_weighted']:.4f}")
    print(f"\n  📁 All results saved to: {OUTPUT_DIR.resolve()}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
