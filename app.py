import gradio as gr
from app.main import app as fastapi_app

# Create a simple dummy interface so Hugging Face recognizes it as a Gradio Space
demo = gr.Interface(
    fn=lambda: "DermAI API is running! Go to /docs to see the Swagger UI.",
    inputs=None,
    outputs="text",
    title="DermAI Backend Active"
)

# Mount our real FastAPI application inside the Gradio space!
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio_ui")
