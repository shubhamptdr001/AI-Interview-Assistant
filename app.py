"""
app.py
------
Streamlit Thin Client for AI Interview Preparation Assistant.
Communicates strictly with the FastAPI backend REST API.
"""

import os
import streamlit as st
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
        "💬 PDF Chat (RAG)",
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

# Optional Groq Key Override
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    user_key = st.sidebar.text_input(
        "🔑 Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Paste your Groq API key or set GROQ_API_KEY in .env",
    )
    if user_key:
        os.environ["GROQ_API_KEY"] = user_key
        st.sidebar.success("Key applied!")
    else:
        st.sidebar.caption("💡 Free key: [console.groq.com/keys](https://console.groq.com/keys)")

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
            with st.spinner("Parsing and analyzing resume via FastAPI backend..."):
                try:
                    # Upload and index via API
                    upload_res = api_client.upload_resume(file_bytes, uploaded_file.name)
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
                        analysis = api_client.analyze_resume(upload_res.get("preview", ""), role=target_role)
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
                    st.error(f"Error communicating with backend: {str(e)}")


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
                    res = api_client.upload_resume(rag_file.getvalue(), rag_file.name)
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
# 🏢 COMPANY QUESTIONS
# ============================================================
elif page == "🏢 Company Questions":
    st.title("🏢 Company-Specific Interview Questions")
    st.write("Enter a company and role — AI will generate realistic interview questions.")

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company Name", placeholder="e.g. Google, TCS, Microsoft")
    with col2:
        role = st.text_input("Role", placeholder="e.g. AI Engineer, Software Developer")

    col3, col4 = st.columns(2)
    with col3:
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
    with col4:
        count = st.slider("Number of Questions", min_value=3, max_value=10, value=5)

    if st.button("Generate Questions", type="primary"):
        if not company.strip() or not role.strip():
            st.warning("Please fill in both Company and Role.")
        else:
            with st.spinner("Generating questions via FastAPI..."):
                try:
                    questions = api_client.generate_company_questions(
                        company=company,
                        role=role,
                        count=count,
                        difficulty=difficulty,
                    )
                    st.markdown("### 📝 Interview Questions")
                    for q in questions:
                        st.markdown(f"- {q}")
                except Exception as e:
                    st.error(f"Error generating questions: {str(e)}")


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
                        with st.spinner("Evaluating answer via backend..."):
                            try:
                                score, feedback = api_client.evaluate_answer(
                                    question=st.session_state.mi_current_question,
                                    answer=answer,
                                    role=st.session_state.mi_role,
                                )
                                st.session_state.mi_scores.append(score)
                                st.success(f"Score: {score}/10")
                                st.write(f"**Feedback:** {feedback}")
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
