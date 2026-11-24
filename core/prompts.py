"""
core/prompts.py
---------------
Centralized, versioned prompt templates for LLM interactions.
"""

PROMPT_VERSION = "1.0.0"

RAG_PROMPT_TEMPLATE = """Tum ek helpful assistant ho jo resume ke content ke base pe sawaal ka jawab de rahe ho.

Resume se related context:
{context}

Sawaal: {question}

Sirf diye gaye context ke base pe Hinglish mein clear, natural jawab do.
Agar context mein jawab na mile to bolo "Ye information resume mein nahi mili."."""


COMPANY_QUESTIONS_PROMPT_TEMPLATE = """Tum ek interview expert ho. "{company}" company ke "{role}" role ke liye
{count} real, commonly asked interview questions do.
Difficulty level: {difficulty}

Numbered list format mein do. Har question ke saath ek line mein bata do
ki ye kis type ka hai (Technical / HR / Behavioral). Hinglish mein likho."""


INTERVIEW_QUESTION_PROMPT_TEMPLATE = """Tum ek technical interviewer ho jo "{role}" role ke liye interview le rahe ho.
Difficulty level: {difficulty}

Pehle ye questions already puche ja chuke hain, inko repeat mat karna:
{previous_questions}

Ek naya, relevant interview question do — sirf question likho, kuch aur nahi, koi numbering nahi."""


EVALUATE_ANSWER_PROMPT_TEMPLATE = """You are an experienced technical interviewer evaluating a candidate for the role of "{role}".

Question: {question}
Candidate's Answer: {answer}

Evaluate the candidate's answer thoroughly in professional, clear English.
Provide your assessment strictly in the following format (do not skip any section):

SCORE: <An integer between 1 and 10 representing overall technical correctness and accuracy>
CORRECT: <1-2 clear sentences in English explaining exactly what the candidate got right>
MISSING: <2-3 clear sentences in English detailing what key concepts, technical depth, edge cases, or details are missing>
FEEDBACK: <Actionable advice in English explaining how the candidate can improve and provide a top-tier answer>"""


CODING_HELP_PROMPT_TEMPLATE = """Tum ek coding mentor ho jo interview preparation mein madad karte ho.

Student ka sawaal: {query}

Clear explanation do. Agar code chahiye to code bhi do (with comments).
Hinglish mein samjhao, simple aur beginner-friendly tone mein."""


RESUME_ANALYSIS_PROMPT_TEMPLATE = """Tum ek expert career coach aur technical recruiter ho.
Neeche diye gaye resume text ko analyze karo targeted role: "{role}" ke liye.

Resume Text:
{resume_text}

Detected Skills:
{detected_skills}

Neeche diye gaye JSON structure mein response do (only valid JSON, no markdown tags, no extra prose):
{{
  "target_role": "{role}",
  "profile_summary": "<2-3 lines summary of candidate profile in English/Hinglish>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "skill_gaps": ["<missing skill 1>", "<missing skill 2>"],
  "actionable_recommendations": ["<recommendation 1>", "<recommendation 2>", "<recommendation 3>"],
  "estimated_match_score": <Integer between 1 and 100>
}}"""
