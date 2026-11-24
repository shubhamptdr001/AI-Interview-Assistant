import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Default to verified active model on Groq
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

_active_model = None


def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def resolve_model(client):
    global _active_model
    if _active_model:
        return _active_model

    env_model = os.getenv("GROQ_MODEL")
    if env_model:
        _active_model = env_model
        return _active_model

    # Priority order of models to try
    preferred_models = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "allam-2-7b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]

    try:
        remote_models = [m.id for m in client.models.list().data]
        for candidate in preferred_models:
            if candidate in remote_models:
                _active_model = candidate
                return _active_model
        # If no preferred model found, pick first non-whisper/non-guard model
        for m in remote_models:
            if "whisper" not in m and "guard" not in m:
                _active_model = m
                return _active_model
    except Exception:
        pass

    _active_model = DEFAULT_MODEL
    return _active_model


def ask_llm(prompt, max_tokens=700):
    client = get_client()
    if not client:
        return (
            "⚠️ Groq API Key nahi mili! Kripya apna GROQ_API_KEY `.env` file mein set karein "
            "ya sidebar mein enter karein. (Get free key: https://console.groq.com/keys)"
        )

    model_to_use = resolve_model(client)
    try:
        response = client.chat.completions.create(
            model=model_to_use,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        err_msg = str(e)
        # If model not found, try fallback to qwen
        if "model_not_found" in err_msg or "404" in err_msg:
            try:
                response = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e2:
                return f"⚠️ Groq API Error: {str(e2)}"
        return f"⚠️ Groq API Error: {err_msg}"


def generate_rag_answer(context_chunks, question):
    context = "\n\n".join(context_chunks)
    prompt = f"""Tum ek helpful assistant ho jo resume ke content ke base pe sawaal ka jawab de rahe ho.

Resume se related context:
{context}

Sawaal: {question}

Sirf diye gaye context ke base pe Hinglish mein clear, natural jawab do.
Agar context mein jawab na mile to bolo "Ye information resume mein nahi mili."."""
    return ask_llm(prompt)


def generate_company_questions(company, role):
    prompt = f"""Tum ek interview expert ho. "{company}" company ke "{role}" role ke liye
5 real, commonly asked interview questions do.

Numbered list format mein do. Har question ke saath ek line mein bata do
ki ye kis type ka hai (Technical / HR / Behavioral). Hinglish mein likho."""
    return ask_llm(prompt, max_tokens=800)


def generate_interview_question(role, difficulty, previous_questions):
    prev_list = "\n".join(previous_questions) if previous_questions else "Koi nahi"
    prompt = f"""Tum ek technical interviewer ho jo "{role}" role ke liye interview le rahe ho.
Difficulty level: {difficulty}

Pehle ye questions already puche ja chuke hain, inko repeat mat karna:
{prev_list}

Ek naya, relevant interview question do — sirf question likho, kuch aur nahi, koi numbering nahi."""
    return ask_llm(prompt, max_tokens=200).strip()


def evaluate_interview_answer(role, question, answer):
    prompt = f"""Tum ek interviewer ho "{role}" role ke liye.

Question: {question}
Candidate ka Answer: {answer}

Is answer ko evaluate karo aur SIRF is exact format mein do, kuch aur mat likho:
SCORE: <0 se 10 ke beech ek number>
FEEDBACK: <2-3 lines mein constructive feedback, Hinglish mein, kya achha tha aur kya improve karna hai>"""

    text = ask_llm(prompt, max_tokens=400)

    score = 0 if "⚠️" in text else 5
    feedback = text
    try:
        for line in text.split("\n"):
            if line.strip().startswith("SCORE:"):
                digits = "".join(filter(str.isdigit, line))
                if digits:
                    score = int(digits)
            if line.strip().startswith("FEEDBACK:"):
                feedback = line.replace("FEEDBACK:", "").strip()
    except Exception:
        pass

    return score, feedback


def coding_help(query):
    prompt = f"""Tum ek coding mentor ho jo interview preparation mein madad karte ho.

Student ka sawaal: {query}

Clear explanation do. Agar code chahiye to code bhi do (with comments).
Hinglish mein samjhao, simple aur beginner-friendly tone mein."""
    return ask_llm(prompt, max_tokens=1000)
