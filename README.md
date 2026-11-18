# 🎯 AI Interview Preparation Assistant

An AI-powered web application that helps students and job-seekers prepare for technical interviews — analyze your resume, chat with it using RAG, generate company-specific questions, get coding help, and practice mock interviews with instant AI feedback.

**🔗 Live Demo:** [https://ai-interview-assistant-tuezhxzz3czavjrqclh9kc.streamlit.app/](#)
**📂 GitHub:** [https://github.com/shubhamptdr001/AI-Interview-Assistant](https://github.com/shubhamptdr001/AI-Interview-Assistant)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **Resume Analyzer** | Upload a PDF/DOCX resume and instantly get word count and detected skills |
| 💬 **Smart PDF Chat (RAG)** | Ask natural-language questions about your resume; powered by FAISS vector search + LLM |
| 🏢 **Company-Specific Questions** | Generate realistic interview questions for any company and role |
| 💻 **Coding Assistant** | Get clear explanations for coding doubts and technical concepts |
| 🎤 **Mock Interview** | Live AI-driven interview practice with instant scoring and feedback |

---

## 🛠️ Tech Stack

- **Frontend/UI:** Streamlit
- **LLM:** Groq API (Llama 3.1)
- **RAG Pipeline:** LangChain, FAISS, HuggingFace Sentence Transformers
- **Resume Parsing:** PyPDF2, python-docx
- **Language:** Python 3.11+

---

## 📁 Project Structure
---

## 🚀 Getting Started (Run Locally)

### 1. Clone the repository
```bash
git clone https://github.com/shubhamptdr001/AI-Interview-Assistant.git
cd AI-Interview-Assistant
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
Create a `.env` file in the root folder:
Get a free key at [console.groq.com](https://console.groq.com).

### 5. Run the app
```bash
streamlit run app.py
```
The app will open at `http://localhost:8501`.

---

## 🧠 How the RAG Pipeline Works

1. Resume text is split into overlapping chunks (`RecursiveCharacterTextSplitter`)
2. Each chunk is converted into a vector embedding (`all-MiniLM-L6-v2`)
3. Embeddings are indexed using **FAISS** for fast similarity search
4. On a user query, the most relevant chunks are retrieved
5. Retrieved chunks + the question are passed to **Groq's Llama 3.1** to generate a natural-language answer

---

## 📌 Future Improvements

- User authentication and saved progress history
- Voice-based mock interview answers (speech-to-text)
- Downloadable PDF report of interview performance
- Support for multiple resume versions/comparisons

---

## 📄 License

This project is open-source and available for learning purposes.
