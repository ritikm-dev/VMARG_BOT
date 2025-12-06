---
title: "VGRAM_BOT"
emoji: "🤖"
colorFrom: "blue"
colorTo: "green"
app_file: app.py
sdk: gradio
sdk_version: 6.0.2
pinned: false
---

# VGRAM_BOT

📌 **Important Instructions**

Before opening the `me` folder, please read the usage notes carefully.

---

## Setup Instructions

1. Create the `me` folder according to the project structure below.
2. Install dependencies:

```bash
pip install -r requirements.txt
Ensure your LinkedIn PDF is named exactly:
Profile (1).pdf

Create a summary.txt file in the me folder and write a short summary about yourself.

Create a .env file in the root folder with the following keys:

makefile
Copy code
GEMINI_API_KEY=
GEMINI_BASE_URL=
PUSHOVER_TOKEN=
PUSHOVER_USER=
Project Structure
bash
Copy code
My-ChatBot
└─ VGRAM_BOT
   ├─ .git/               # Git repository files
   ├─ app.py              # Main chatbot script
   ├─ requirements.txt    # Python dependencies
   ├─ venv/               # Virtual environment
   ├─ .env                # Environment variables
   └─ me/
      ├─ Profile (1).pdf  # Your LinkedIn PDF (can change name in app.py)
      └─ summary.txt      # Your summary file
