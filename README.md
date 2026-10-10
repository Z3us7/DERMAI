# DermAI API Server — Operating Instructions

Welcome to your production-grade DermAI backend! This document contains everything you need to know about starting the server, accessing the User Interface (UI), and analyzing images.

## 🔗 Server Links

- **Main User Interface (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Documentation (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

*(Note: The server must be running to access these links!)*

---

## 🚀 How to Start the Server

Whenever you want to start the API, open your **PowerShell** terminal, ensure you are in the `DermAI OG` directory, and run this exact command:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**You will know it is working when you see:**
> `INFO: Application startup complete.`
> `=== Model loaded in ... ms. API ready. ===`

To **Stop** the server at any time, click on your terminal and press `CTRL + C`.

---

## 🖥️ How to Use the UI (Test an Image)

FastAPI provides a beautiful, interactive web interface where you can test your model without writing any extra code.

1. **Open the UI:** Go to [http://localhost:8000/docs](http://localhost:8000/docs) in your web browser.
2. **Find the Endpoint:** You will see a green box labeled `POST /api/v1/analyze`. Click on it to expand it.
3. **Try it Out:** Click the **"Try it out"** button in the top right corner of the expanded box.
4. **Upload Image:** You will see a file upload button labeled `image`. Click **"Choose File"** and select a skin image (JPEG or PNG) from your computer.
5. **Execute:** Click the large blue **"Execute"** button below the file uploader.
6. **View Results:** Scroll down slightly to the **"Server response"** section. You will see a JSON block containing your model's prediction, the confidence score, and the LLM's patient-friendly explanation!

---

## 🛠️ Other Useful Commands

If you ever need to verify the code quality or run the test suite, use these commands in PowerShell:

**Run all 51 automated tests:**
```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

**Run the Linter (checks for errors):**
```powershell
.\venv\Scripts\python.exe -m ruff check app/ tests/
```

**Format the code:**
```powershell
.\venv\Scripts\python.exe -m black app/ tests/
```

---

## 🤖 Activating the Real AI Explanations

Right now, the LLM is providing a `[MOCK LLM RESPONSE]`. To activate real GPT-4 explanations:
1. Open the `.env` file (create one by copying `.env.example` if you haven't already).
2. Add your real OpenAI API key: `OPENAI_API_KEY=sk-...`
3. Save the file. The server will automatically reload and start using the real AI!
