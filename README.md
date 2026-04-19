# 🚀 CareerForge AI

An AI-powered career preparation platform that helps students and developers **analyze resumes, improve ATS scores, and practice interviews** using modern GenAI tools.

---

## ✨ Features

### 📄 Resume Analyzer (Module 1)

* Extracts skills from resume (PDF)
* Calculates **ATS Score (Hybrid approach)**
* Matches with relevant job roles
* Shows:

  * ✅ Matched skills
  * 📊 ATS breakdown
* Custom role analysis (user-defined roles)

---

### 🤖 AI Interview Simulator (Module 2)

* Role-based interview questions
* Supports different rounds (technical / HR)
* Uses **RAG (Retrieval-Augmented Generation)**
* Avoids repeated questions
* Maintains session-based conversation

---

## 🧠 Tech Stack

### Backend

* **FastAPI**
* **Groq LLaMA3 (LLM)**
* **HuggingFace Embeddings**
* **ChromaDB (Vector DB)**

### Frontend

* HTML + CSS + JavaScript
* Jinja2 Templates

### AI Components

* Skill extraction (rule-based + LLM)
* Role matching engine
* RAG pipeline for interview system

---



---

## ⚙️ Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/your-username/careerforge-ai.git
cd careerforge-ai
```

---

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Add environment variables

Create `.env` file:

```
GROQ_API_KEY=your_groq_key
HF_API_KEY=your_huggingface_key
SECRET_KEY=your_secret_key
```

---

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

---

### 6. Open in browser

```
http://127.0.0.1:8000
```

---

## 📊 ATS Scoring Logic (Hybrid)

Score is calculated using:

* Skills coverage
* Role match percentage
* Resume quality (length + sections)
* Project quality (LLM-based evaluation)
* Bonus factors (GitHub, experience, etc.)

---

## 🔥 Key Highlights

* Hybrid AI + rule-based system
* Real-time resume analysis
* Skill gap detection
* Interactive interview system
* Clean modern UI

---

## 📌 Future Improvements

* Resume rewriting suggestions
* Job recommendation system
* Company-specific interview prep
* User authentication & dashboard

---

## 👨‍💻 Contributors- 

**Anurodh Jatav**
**Jewel Rachel Sunny**

---

## ⭐ If you like this project

Give it a star ⭐ on GitHub and share it!

---
