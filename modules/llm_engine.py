import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"


def ask_llm(prompt, max_tokens=700):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


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

    score = 5
    feedback = text
    try:
        for line in text.split("\n"):
            if line.strip().startswith("SCORE:"):
                digits = ''.join(filter(str.isdigit, line))
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