import streamlit as st
from utils.config import APP_NAME
from modules.resume_analyzer import extract_text, extract_skills, get_word_count
from modules.rag_engine import build_vector_store, search_similar_chunks
from modules.llm_engine import (
    generate_rag_answer,
    generate_company_questions,
    coding_help,
    generate_interview_question,
    evaluate_interview_answer,
)

st.set_page_config(page_title=APP_NAME, page_icon="🎯", layout="wide")

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
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit + Groq LLM")

# ============================================================
# HOME PAGE
# ============================================================
if page == "🏠 Home":
    st.title("🎯 AI Interview Preparation Assistant")
    st.markdown("##### Prepare smarter for your next interview with the power of AI")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📄 Resume Analyzer")
        st.write("Upload your resume and get instant AI-powered analysis, skill detection, and insights.")

    with col2:
        st.markdown("### 💬 Smart PDF Chat")
        st.write("Ask questions directly about your resume — the AI reads it and responds naturally.")

    with col3:
        st.markdown("### 🎤 Mock Interview")
        st.write("Practice live with AI — get real-time questions, instant scoring, and constructive feedback.")

    st.markdown("---")

    col4, col5 = st.columns(2)
    with col4:
        st.markdown("### 🏢 Company-Specific Questions")
        st.write("Generate targeted interview questions for any company and role.")

    with col5:
        st.markdown("### 💻 Coding Assistant")
        st.write("Get clear, simple explanations for coding doubts and technical concepts.")

    st.markdown("---")
    st.markdown("#### 🚀 Choose a section from the sidebar to get started")

# ============================================================
# RESUME ANALYZER
# ============================================================
elif page == "📄 Resume Analyzer":
    st.title("📄 Resume Analyzer")
    st.write("Upload your resume (PDF or DOCX) to get an instant analysis.")

    uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"], key="analyzer_upload")

    if uploaded_file is not None:
        with st.spinner("Reading your resume..."):
            resume_text = extract_text(uploaded_file)

        if resume_text is None or resume_text.strip() == "":
            st.error("Could not extract text. The file may be corrupted or a scanned image.")
        else:
            st.success("Resume parsed successfully!")

            col1, col2 = st.columns(2)
            col1.metric("Total Words", get_word_count(resume_text))

            skills_found = extract_skills(resume_text)
            col2.metric("Skills Detected", len(skills_found))

            st.markdown("### 🛠️ Detected Skills")
            if skills_found:
                st.write(", ".join([f"`{s}`" for s in skills_found]))
            else:
                st.warning("No known skills matched. Consider expanding the skills bank.")

            with st.expander("📄 View Extracted Raw Text"):
                st.text_area("Resume Text", resume_text, height=300)

# ============================================================
# PDF CHAT (RAG)
# ============================================================
elif page == "💬 PDF Chat (RAG)":
    st.title("💬 PDF Chat (RAG)")
    st.write("Upload your resume, then ask questions about it — powered by retrieval-augmented generation.")

    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None

    rag_file = st.file_uploader("Upload your resume for RAG", type=["pdf", "docx"], key="rag_upload")

    if rag_file is not None:
        if st.button("📚 Process Resume", type="primary"):
            with st.spinner("Building embeddings..."):
                text = extract_text(rag_file)
                st.session_state.vector_store = build_vector_store(text)
            st.success("Resume processed! You can now ask questions below.")

    if st.session_state.vector_store is not None:
        st.markdown("---")
        query = st.text_input("Ask a question (e.g. 'What projects have I worked on?')")

        if st.button("🔍 Search & Answer"):
            if query.strip() == "":
                st.warning("Please type a question first.")
            else:
                with st.spinner("Searching your resume..."):
                    chunks = search_similar_chunks(st.session_state.vector_store, query, k=3)

                with st.spinner("Generating AI answer..."):
                    ai_answer = generate_rag_answer(chunks, query)

                st.markdown("### 🤖 AI Answer")
                st.success(ai_answer)

                with st.expander("📌 View source excerpts used"):
                    for i, chunk in enumerate(chunks, 1):
                        st.markdown(f"**Match {i}:**")
                        st.info(chunk)

# ============================================================
# COMPANY QUESTIONS
# ============================================================
elif page == "🏢 Company Questions":
    st.title("🏢 Company-Specific Interview Questions")
    st.write("Enter a company and role — AI will generate realistic interview questions.")

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company Name", placeholder="e.g. TCS, Infosys, Google")
    with col2:
        role = st.text_input("Role", placeholder="e.g. AI Engineer, Software Developer")

    if st.button("Generate Questions", type="primary"):
        if not company or not role:
            st.warning("Please fill in both Company and Role.")
        else:
            with st.spinner("Generating questions..."):
                questions = generate_company_questions(company, role)
            st.markdown("### 📝 Interview Questions")
            st.markdown(questions)

# ============================================================
# CODING ASSISTANT
# ============================================================
elif page == "💻 Coding Assistant":
    st.title("💻 Coding Assistant")
    st.write("Ask any coding doubt — DSA, concepts, or code explanations.")

    coding_query = st.text_area("Type your coding question", height=100,
                                  placeholder="e.g. 'What is the difference between list and tuple in Python?'")

    if st.button("Solve", type="primary"):
        if not coding_query.strip():
            st.warning("Please type your question first.")
        else:
            with st.spinner("Thinking..."):
                answer = coding_help(coding_query)
            st.markdown("### 💡 Answer")
            st.markdown(answer)

# ============================================================
# MOCK INTERVIEW
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
            role_input = st.text_input("Role (e.g. AI Engineer, IoT Developer)")
        with col2:
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

        if st.button("🚀 Start Interview", type="primary"):
            if not role_input.strip():
                st.warning("Please enter a role first.")
            else:
                st.session_state.mi_role = role_input
                st.session_state.mi_difficulty = difficulty
                st.session_state.mi_started = True
                with st.spinner("Preparing the first question..."):
                    q = generate_interview_question(role_input, difficulty, [])
                st.session_state.mi_current_question = q
                st.session_state.mi_questions.append(q)
                st.rerun()

    else:
        st.info(f"**Role:** {st.session_state.mi_role} | **Difficulty:** {st.session_state.mi_difficulty} | **Question:** {len(st.session_state.mi_questions)}")

        st.markdown(f"### ❓ {st.session_state.mi_current_question}")
        answer = st.text_area("Type your answer", height=150, key=f"answer_{len(st.session_state.mi_questions)}")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Submit Answer", type="primary"):
                if not answer.strip():
                    st.warning("Please write an answer first.")
                else:
                    with st.spinner("Evaluating..."):
                        score, feedback = evaluate_interview_answer(
                            st.session_state.mi_role,
                            st.session_state.mi_current_question,
                            answer
                        )
                    st.session_state.mi_scores.append(score)
                    st.success(f"Score: {score}/10")
                    st.write(f"**Feedback:** {feedback}")

        with col2:
            if st.button("➡️ Next Question"):
                with st.spinner("Preparing next question..."):
                    q = generate_interview_question(
                        st.session_state.mi_role,
                        st.session_state.mi_difficulty,
                        st.session_state.mi_questions
                    )
                st.session_state.mi_current_question = q
                st.session_state.mi_questions.append(q)
                st.rerun()

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