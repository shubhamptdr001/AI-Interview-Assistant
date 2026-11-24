"""
app.py
------
Streamlit Thin Client for AI Interview Preparation Assistant.
Communicates strictly with the FastAPI backend REST API.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Automatically load environment variables from .env
load_dotenv()

from client.api_client import api_client, BACKEND_URL

APP_NAME = "AI Interview Assistant"

st.set_page_config(page_title=APP_NAME, page_icon="🎯", layout="wide")

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("🎯 AI Interview Assistant")
page = st.sidebar.radio(
    "Choose a section:",
    [
        "🏠 Home",
        "📄 Resume Analyzer",
        "💬 PDF Chat",
        "🏢 Company Questions",
        "💻 Coding Assistant",
        "🎤 Mock Interview",
    ],
)

st.sidebar.markdown("---")

# Backend Health & Connectivity Check
health = api_client.check_health()
if health:
    st.sidebar.success(f"🟢 API Connected ({health.get('model', 'Groq')})", icon="✅")
else:
    st.sidebar.warning(f"🟡 Backend Offline at `{BACKEND_URL}`")
    st.sidebar.caption("Run backend with: `uvicorn api.main:app --reload`")

st.sidebar.markdown("---")
st.sidebar.caption("Architecture: Streamlit (Client) ➔ FastAPI ➔ Core / Groq")


# ============================================================
# 🏠 HOME PAGE
# ============================================================
if page == "🏠 Home":
    st.title("🎯 AI Interview Preparation Assistant")
    st.markdown("##### Prepare smarter for your next technical interview with AI-powered tools")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📄 Resume Analyzer")
        st.write("Upload your resume and get instant skill detection, word counts, and role gap analysis.")

    with col2:
        st.markdown("### 💬 Smart PDF Chat (RAG)")
        st.write("Ask questions directly about your resume — powered by retrieval-augmented generation.")

    with col3:
        st.markdown("### 🎤 Mock Interview")
        st.write("Practice real-time technical questions with instant scoring and constructive feedback.")

    st.markdown("---")

    col4, col5 = st.columns(2)
    with col4:
        st.markdown("### 🏢 Company Questions")
        st.write("Generate targeted interview questions tailored to any company and role.")

    with col5:
        st.markdown("### 💻 Coding Assistant")
        st.write("Get clear explanations for coding doubts and technical interview concepts.")

    st.markdown("---")
    st.info("💡 **Getting Started**: Choose a module from the left sidebar to begin.")


# ============================================================
# 📄 RESUME ANALYZER
# ============================================================
elif page == "📄 Resume Analyzer":
    st.title("📄 Resume Analyzer")
    st.write("Upload your resume (PDF or DOCX) to get an instant analysis via the backend.")

    uploaded_file = st.file_uploader(
        "Upload your resume", type=["pdf", "docx"], key="analyzer_upload"
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        target_role = st.text_input("Target Role (optional, for gap analysis)", placeholder="e.g. AI Engineer, Full-Stack Developer")

        if st.button("📊 Analyze Resume", type="primary"):
            with st.spinner("Analyzing resume..."):
                try:
                    # Instant upload without building unnecessary RAG vector index
                    upload_res = api_client.upload_resume(file_bytes, uploaded_file.name, index_for_rag=False)
                    st.success("Resume parsed successfully!")

                    col1, col2 = st.columns(2)
                    col1.metric("Total Words", upload_res.get("word_count", 0))
                    skills = upload_res.get("detected_skills", [])
                    col2.metric("Skills Detected", len(skills))

                    st.markdown("### 🛠️ Detected Skills")
                    if skills:
                        st.write(", ".join([f"`{s}`" for s in skills]))
                    else:
                        st.warning("No known skills matched.")

                    # Deep analysis if role provided
                    if target_role.strip():
                        full_resume_text = upload_res.get("text") or upload_res.get("preview", "")
                        analysis = api_client.analyze_resume(full_resume_text, role=target_role)
                        st.markdown("---")
                        st.markdown(f"### 🎯 Role Match Assessment: **{target_role}**")
                        st.metric("Estimated Match Score", f"{analysis.get('estimated_match_score', 0)}/100")
                        
                        col_s, col_g = st.columns(2)
                        with col_s:
                            st.markdown("#### ✅ Strengths")
                            for s in analysis.get("strengths", []):
                                st.write(f"- {s}")
                        with col_g:
                            st.markdown("#### ⚠️ Skill Gaps")
                            for g in analysis.get("skill_gaps", []):
                                st.write(f"- {g}")

                    with st.expander("📄 View Extracted Text Preview"):
                        st.text_area("Preview", upload_res.get("preview", ""), height=200)

                except Exception as e:
                    st.error(f"Error analyzing resume: {str(e)}")


# ============================================================
# 💬 PDF CHAT (RAG)
# ============================================================
elif page == "💬 PDF Chat (RAG)":
    st.title("💬 PDF Chat (RAG)")
    st.write("Upload your resume, then ask questions about it — powered by retrieval-augmented generation.")

    if "rag_session_id" not in st.session_state:
        st.session_state.rag_session_id = None
        st.session_state.rag_filename = None

    rag_file = st.file_uploader(
        "Upload your resume for RAG", type=["pdf", "docx"], key="rag_upload"
    )

    if rag_file is not None:
        if st.button("📚 Process Resume", type="primary"):
            with st.spinner("Building embeddings and vector store in backend..."):
                try:
                    res = api_client.upload_resume(rag_file.getvalue(), rag_file.name, index_for_rag=True)
                    st.session_state.rag_session_id = res["session_id"]
                    st.session_state.rag_filename = rag_file.name
                    st.success(f"Resume '{rag_file.name}' indexed! You can now ask questions below.")
                except Exception as e:
                    st.error(f"Processing failed: {str(e)}")

    if st.session_state.rag_session_id:
        st.caption(f"Active Session: `{st.session_state.rag_session_id[:12]}...` ({st.session_state.rag_filename})")
        st.markdown("---")
        query = st.text_input("Ask a question about your resume (e.g. 'What projects have I worked on?')")

        if st.button("🔍 Search & Answer", type="primary"):
            if not query.strip():
                st.warning("Please type a question first.")
            else:
                with st.spinner("Retrieving excerpts and generating answer..."):
                    try:
                        ans = api_client.ask_resume(
                            session_id=st.session_state.rag_session_id,
                            question=query,
                        )
                        st.markdown("### 🤖 AI Answer")
                        st.success(ans["answer"])

                        sources = ans.get("sources", [])
                        if sources:
                            with st.expander("📌 View source excerpts used"):
                                for i, chunk in enumerate(sources, 1):
                                    st.markdown(f"**Match {i}:**")
                                    st.info(chunk)
                    except Exception as e:
                        st.error(f"Query error: {str(e)}")


# ============================================================
# 🏢 COMPANY QUESTIONS (INTERACTIVE PRACTICE)
# ============================================================
elif page == "🏢 Company Questions":
    st.title("🏢 Company-Specific Interview Practice")
    st.write("Generate targeted interview questions for any company and practice them one-by-one with instant AI feedback in English.")

    # Initialize session state for interactive company questions
    if "cq_active" not in st.session_state:
        st.session_state.cq_active = False
        st.session_state.cq_questions = []
        st.session_state.cq_idx = 0
        st.session_state.cq_company = ""
        st.session_state.cq_role = ""
        st.session_state.cq_difficulty = "Medium"
        st.session_state.cq_evaluations = {}
        st.session_state.cq_answers = {}

    if not st.session_state.cq_active:
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company Name", placeholder="e.g. Google, TCS, Microsoft", value=st.session_state.cq_company)
        with col2:
            role = st.text_input("Role", placeholder="e.g. AI Engineer, Software Developer", value=st.session_state.cq_role)

        col3, col4 = st.columns(2)
        with col3:
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
        with col4:
            count = st.slider("Number of Questions", min_value=3, max_value=10, value=5)

        if st.button("🚀 Start Practice Session", type="primary"):
            if not company.strip() or not role.strip():
                st.warning("Please fill in both Company and Role.")
            else:
                with st.spinner("Generating targeted questions via AI..."):
                    try:
                        questions = api_client.generate_company_questions(
                            company=company,
                            role=role,
                            count=count,
                            difficulty=difficulty,
                        )
                        if questions:
                            st.session_state.cq_questions = questions
                            st.session_state.cq_idx = 0
                            st.session_state.cq_company = company
                            st.session_state.cq_role = role
                            st.session_state.cq_difficulty = difficulty
                            st.session_state.cq_evaluations = {}
                            st.session_state.cq_answers = {}
                            st.session_state.cq_active = True
                            st.rerun()
                        else:
                            st.error("No questions could be generated. Please try again.")
                    except Exception as e:
                        st.error(f"Error generating questions: {str(e)}")

    else:
        # Active One-by-One Question Session
        total_q = len(st.session_state.cq_questions)
        curr_idx = st.session_state.cq_idx
        curr_q = st.session_state.cq_questions[curr_idx]

        # Top progress bar and header
        st.info(
            f"🏢 **{st.session_state.cq_company}** | 🎯 **{st.session_state.cq_role}** | "
            f"📊 **Difficulty:** {st.session_state.cq_difficulty} | **Question {curr_idx + 1} of {total_q}**"
        )
        st.progress((curr_idx + 1) / total_q)

        st.markdown(f"### ❓ Question {curr_idx + 1}")
        st.markdown(f"**{curr_q}**")

        # Answer text box for the current question
        saved_answer = st.session_state.cq_answers.get(curr_idx, "")
        user_answer = st.text_area(
            "Your Answer:",
            value=saved_answer,
            height=160,
            key=f"cq_ans_box_{curr_idx}",
            placeholder="Type your technical response in English...",
        )

        # Action Buttons
        col_submit, col_prev, col_next, col_reset = st.columns([2, 1, 1, 1])

        with col_submit:
            if st.button("✅ Submit Answer", type="primary", key=f"btn_sub_{curr_idx}"):
                if not user_answer.strip():
                    st.warning("Please type an answer before submitting.")
                else:
                    st.session_state.cq_answers[curr_idx] = user_answer
                    with st.spinner("Evaluating your response..."):
                        try:
                            eval_res = api_client.evaluate_answer(
                                question=curr_q,
                                answer=user_answer,
                                role=st.session_state.cq_role,
                            )
                            st.session_state.cq_evaluations[curr_idx] = eval_res
                            st.rerun()
                        except Exception as e:
                            st.error(f"Evaluation error: {str(e)}")

        with col_prev:
            if st.button("⬅️ Previous", disabled=(curr_idx == 0), key=f"btn_prev_{curr_idx}"):
                st.session_state.cq_answers[curr_idx] = user_answer
                st.session_state.cq_idx = max(0, curr_idx - 1)
                st.rerun()

        with col_next:
            if st.button("Next ➡️", disabled=(curr_idx >= total_q - 1), key=f"btn_next_{curr_idx}"):
                st.session_state.cq_answers[curr_idx] = user_answer
                st.session_state.cq_idx = min(total_q - 1, curr_idx + 1)
                st.rerun()

        with col_reset:
            if st.button("🏁 End Session", key=f"btn_end_{curr_idx}"):
                st.session_state.cq_active = False
                st.rerun()

        # Display Evaluation if submitted for current question
        if curr_idx in st.session_state.cq_evaluations:
            eval_data = st.session_state.cq_evaluations[curr_idx]
            score = eval_data.get("score", 5)
            pct = eval_data.get("correctness_percent", score * 10)

            st.markdown("---")
            st.markdown("### 📊 Evaluation Feedback (in English)")

            # Score metric
            if score >= 7:
                st.success(f"🎯 **Score: {score}/10 — {pct}% Correct**", icon="✅")
            elif score >= 4:
                st.warning(f"⚠️ **Score: {score}/10 — {pct}% Correct**", icon="⚡")
            else:
                st.error(f"❌ **Score: {score}/10 — {pct}% Correct**", icon="⚠️")

            # Two distinct columns for What was correct & What's missing
            col_c, col_m = st.columns(2)
            with col_c:
                st.markdown("#### ✅ What was correct:")
                correct_text = eval_data.get("what_was_good") or "Key fundamentals were mentioned."
                st.info(correct_text)

            with col_m:
                st.markdown("#### 🔍 What was missing:")
                missing_text = eval_data.get("what_is_missing") or "Consider adding edge cases and architectural trade-offs."
                st.warning(missing_text)

            # Detailed Mentor Feedback
            with st.expander("💡 View Detailed Mentor Feedback"):
                st.write(eval_data.get("feedback", ""))


# ============================================================
# 💻 CODING ASSISTANT
# ============================================================
elif page == "💻 Coding Assistant":
    st.title("💻 Coding Assistant")
    st.write("Ask any coding doubt — DSA, concepts, or code explanations.")

    coding_query = st.text_area(
        "Type your coding question",
        height=120,
        placeholder="e.g. 'What is the difference between list and tuple in Python?' or 'Write binary search in Python'",
    )

    if st.button("Solve", type="primary"):
        if not coding_query.strip():
            st.warning("Please type your question first.")
        else:
            with st.spinner("Solving with AI..."):
                try:
                    ans = api_client.get_coding_help(coding_query)
                    st.markdown("### 💡 Answer")
                    st.markdown(ans)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


# ============================================================
# 🎤 MOCK INTERVIEW
# ============================================================
elif page == "🎤 Mock Interview":
    st.title("🎤 Mock Interview")
    st.write("Enter a role — the AI will ask questions, evaluate your answers, and give instant feedback.")

    if "mi_role" not in st.session_state:
        st.session_state.mi_role = ""
        st.session_state.mi_questions = []
        st.session_state.mi_scores = []
        st.session_state.mi_current_question = None
        st.session_state.mi_started = False

    if not st.session_state.mi_started:
        col1, col2 = st.columns(2)
        with col1:
            role_input = st.text_input("Role (e.g. Software Engineer, AI Engineer)")
        with col2:
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

        if st.button("🚀 Start Interview", type="primary"):
            if not role_input.strip():
                st.warning("Please enter a role first.")
            else:
                st.session_state.mi_role = role_input
                st.session_state.mi_difficulty = difficulty
                st.session_state.mi_started = True
                with st.spinner("Preparing first question..."):
                    try:
                        q = api_client.get_interview_question(role_input, difficulty, [])
                        st.session_state.mi_current_question = q
                        st.session_state.mi_questions.append(q)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to start interview: {str(e)}")

    else:
        st.info(
            f"**Role:** {st.session_state.mi_role} | **Difficulty:** {st.session_state.mi_difficulty} | "
            f"**Question:** {len(st.session_state.mi_questions)}"
        )

        # Handle API error gracefully
        if st.session_state.mi_current_question and st.session_state.mi_current_question.startswith("⚠️"):
            st.error(st.session_state.mi_current_question)
            col_retry, col_reset = st.columns(2)
            with col_retry:
                if st.button("🔄 Retry Question", type="primary"):
                    with st.spinner("Regenerating question..."):
                        prev = st.session_state.mi_questions[:-1] if len(st.session_state.mi_questions) > 1 else []
                        q = api_client.get_interview_question(
                            st.session_state.mi_role, st.session_state.mi_difficulty, prev
                        )
                        st.session_state.mi_current_question = q
                        if st.session_state.mi_questions:
                            st.session_state.mi_questions[-1] = q
                    st.rerun()
            with col_reset:
                if st.button("🔄 Restart Interview"):
                    st.session_state.mi_started = False
                    st.session_state.mi_questions = []
                    st.session_state.mi_scores = []
                    st.session_state.mi_current_question = None
                    st.rerun()
        else:
            st.markdown(f"### ❓ {st.session_state.mi_current_question}")
            answer = st.text_area(
                "Type your answer", height=150, key=f"answer_{len(st.session_state.mi_questions)}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Submit Answer", type="primary"):
                    if not answer.strip():
                        st.warning("Please write an answer first.")
                    else:
                        with st.spinner("Evaluating answer in English..."):
                            try:
                                eval_data = api_client.evaluate_answer(
                                    question=st.session_state.mi_current_question,
                                    answer=answer,
                                    role=st.session_state.mi_role,
                                )
                                score = eval_data.get("score", 5)
                                pct = eval_data.get("correctness_percent", score * 10)
                                st.session_state.mi_scores.append(score)

                                if score >= 7:
                                    st.success(f"🎯 **Score: {score}/10 — {pct}% Correct**", icon="✅")
                                elif score >= 4:
                                    st.warning(f"⚠️ **Score: {score}/10 — {pct}% Correct**", icon="⚡")
                                else:
                                    st.error(f"❌ **Score: {score}/10 — {pct}% Correct**", icon="⚠️")

                                col_cg, col_cm = st.columns(2)
                                with col_cg:
                                    st.markdown("#### ✅ What was correct:")
                                    st.info(eval_data.get("what_was_good", "Good attempt covering the basics."))
                                with col_cm:
                                    st.markdown("#### 🔍 What was missing:")
                                    st.warning(eval_data.get("what_is_missing", "Consider adding more technical depth."))

                                with st.expander("💡 Detailed Feedback"):
                                    st.write(eval_data.get("feedback", ""))
                            except Exception as e:
                                st.error(f"Evaluation failed: {str(e)}")

            with col2:
                if st.button("➡️ Next Question"):
                    with st.spinner("Preparing next question..."):
                        try:
                            q = api_client.get_interview_question(
                                st.session_state.mi_role,
                                st.session_state.mi_difficulty,
                                st.session_state.mi_questions,
                            )
                            st.session_state.mi_current_question = q
                            st.session_state.mi_questions.append(q)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not load question: {str(e)}")

            with col3:
                if st.button("🏁 End Interview"):
                    st.session_state.mi_started = False
                    st.markdown("## 📊 Interview Summary")
                    total = len(st.session_state.mi_scores)
                    if total > 0:
                        avg = sum(st.session_state.mi_scores) / total
                        st.metric("Questions Attempted", total)
                        st.metric("Average Score", round(avg, 1))
                    else:
                        st.write("No answers were submitted.")

                    st.session_state.mi_questions = []
                    st.session_state.mi_scores = []
                    st.session_state.mi_current_question = None
