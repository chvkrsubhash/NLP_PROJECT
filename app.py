# app.py
import streamlit as st
import random
import base64
import os
from datetime import datetime
from config import WELCOME_MESSAGES, RESUME_PROMPTS, SKILL_MESSAGES, INTERVIEW_START_MESSAGES, QUESTION_TRANSITIONS
from utils import extract_text_from_pdf, extract_text_from_docx, generate_technical_questions, format_skills_message, get_feedback_message
from evaluate import evaluate_answer
from export import export_results_as_pdf, send_email
from auth import login

# Set page config
st.set_page_config(page_title="Technical Interview Chatbot", layout="wide")

# Session state initialization
def initialize_session_state():
    defaults = {
        "resume_text": "",
        "skills": {},
        "questions": [],
        "current_question_index": 0,
        "evaluations": {},
        "interview_complete": False,
        "interview_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "chat_messages": [{"role": "assistant", "content": random.choice(WELCOME_MESSAGES) + " " + random.choice(RESUME_PROMPTS)}],
        "candidate_name": "",
        "bot_state": "wait_for_resume",
        "max_questions": 5,
        "debug_skills": [],
        "raw_resume_text": "",
        "interview_history": [],
        "user": None,
        "user_email": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

def add_message(role, content):
    st.session_state.chat_messages.append({"role": role, "content": content})

# Main app
def main():
    if not login():
        return

    # Sidebar
    with st.sidebar:
        st.header("Interview Settings")
        if st.session_state.bot_state in ["wait_for_resume", "analyzing_resume"]:
            st.info("Upload or paste your resume to begin.")
        elif st.session_state.bot_state == "interview":
            st.subheader("Progress")
            progress = st.session_state.current_question_index / len(st.session_state.questions)
            st.progress(progress)
            st.write(f"Question {st.session_state.current_question_index}/{len(st.session_state.questions)}")
            if st.session_state.skills:
                st.subheader("Skills Focus")
                for category, skills in st.session_state.skills.items():
                    with st.expander(category.capitalize()):
                        st.write(", ".join(skills))
        elif st.session_state.bot_state == "complete":
            st.success("Interview Complete!")
            evaluations = st.session_state.evaluations
            total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
            avg_score = total_score / len(evaluations) if evaluations else 0
            rating = "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement"
            st.metric("Overall Score", f"{avg_score:.1f}/100")
            st.metric("Rating", rating)

        max_q = st.slider("Number of Questions", min_value=3, max_value=10, value=st.session_state.max_questions)
        if max_q != st.session_state.max_questions:
            st.session_state.max_questions = max_q

        st.subheader("Interview History")
        if st.session_state.interview_history:
            for idx, record in enumerate(st.session_state.interview_history):
                with st.expander(f"Interview {idx+1}: {record['candidate_name']} ({record['date']})"):
                    st.write(f"**Average Score:** {record['avg_score']:.1f}/100")
                    st.write(f"**Rating:** {record['rating']}")
                    st.write("**Skills:**")
                    for category, skills in record['skills'].items():
                        st.write(f"- {category.capitalize()}: {', '.join(skills)}")
                    st.write("**Questions and Scores:**")
                    for i, q in enumerate(record['questions']):
                        if q['question'] in record['evaluations']:
                            eval_data = record['evaluations'][q['question']]
                            st.write(f"- Q{i+1}: {q['question']} (Score: {eval_data['evaluation'].get('score', 0)}/100)")
                    if st.button(f"Download PDF (Interview {idx+1})", key=f"download_{idx}"):
                        try:
                            pdf_path = export_results_as_pdf(record)
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            pdf_b64 = base64.b64encode(pdf_bytes).decode()
                            st.markdown(f'<a href="data:application/pdf;base64,{pdf_b64}" download="{os.path.basename(pdf_path)}">Download PDF</a>', unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"PDF generation error: {e}")

        if st.button("Start New Interview"):
            initialize_session_state()
            st.rerun()

        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.user_email = None
            st.rerun()

    # Main UI
    st.title("Technical Interview Chatbot 🤖")
    uploaded_file = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"], key="resume_upload")
    chat_container = st.container()

    def process_user_input(user_input):
        from utils import extract_skills
        add_message("user", user_input)

        if st.session_state.bot_state == "wait_for_resume":
            if len(user_input.split()) <= 3 and len(st.session_state.chat_messages) <= 3:
                st.session_state.candidate_name = user_input
                add_message("assistant", f"Hi {user_input}! Please upload or paste your resume.")
                return

            st.session_state.resume_text = user_input
            st.session_state.bot_state = "analyzing_resume"
            add_message("assistant", "Analyzing your resume for skills...")

            skills = extract_skills(user_input)
            if not skills:
                add_message("assistant", "No technical skills found. List some skills (e.g., Python, Java, AWS).")
                st.session_state.bot_state = "manual_skills"
            else:
                st.session_state.skills = skills
                skill_message = random.choice(SKILL_MESSAGES) + "\n\n" + format_skills_message(skills)
                if st.session_state.debug_skills:
                    skill_message += "\n\n**Debug Info:**\n" + "\n".join(st.session_state.debug_skills)
                skill_message += "\n\nAre these correct? Add more skills or type 'start interview'."
                add_message("assistant", skill_message)
                st.session_state.bot_state = "confirm_skills"

        elif st.session_state.bot_state == "manual_skills":
            from config import COMMON_SKILLS
            skills_input = user_input.lower()
            manual_skills = {}
            for category, skill_list in COMMON_SKILLS.items():
                found_skills = [skill for skill in skill_list if skill in skills_input]
                if found_skills:
                    manual_skills[category] = found_skills

            if not manual_skills:
                manual_skills = {'programming': ['python'], 'tools': ['git']}

            st.session_state.skills = manual_skills
            skill_message = "Added skills:\n\n" + format_skills_message(manual_skills) + "\n\nType 'start interview' to begin."
            add_message("assistant", skill_message)
            st.session_state.bot_state = "confirm_skills"

        elif st.session_state.bot_state == "confirm_skills":
            if any(x in user_input.lower() for x in ["start interview", "ready", "yes"]):
                technical_questions = generate_technical_questions(st.session_state.skills, st.session_state.max_questions)
                st.session_state.questions = technical_questions
                st.session_state.current_question_index = 0
                first_question = technical_questions[0]["question"] if technical_questions else "Tell me about your tech background."
                add_message("assistant", f"{random.choice(INTERVIEW_START_MESSAGES)}\n\n**Question 1:** {first_question}")
                st.session_state.bot_state = "interview"
            else:
                new_skills = extract_skills(user_input)
                if new_skills:
                    for category, skills_list in new_skills.items():
                        if category in st.session_state.skills:
                            st.session_state.skills[category].extend([s for s in skills_list if s not in st.session_state.skills[category]])
                        else:
                            st.session_state.skills[category] = skills_list
                    add_message("assistant", "Skills updated. Type 'start interview' to begin.")
                else:
                    add_message("assistant", "Type 'start interview' when ready.")

        elif st.session_state.bot_state == "interview":
            current_index = st.session_state.current_question_index
            current_question = st.session_state.questions[current_index]
            evaluation = evaluate_answer(
                question=current_question['question'],
                answer=user_input,
                expected_keywords=current_question['expected_keywords']
            )
            st.session_state.evaluations[current_question['question']] = {"answer": user_input, "evaluation": evaluation}

            score = evaluation.get('score', 0)
            feedback = f"{get_feedback_message(score)}\n\n**Score:** {score}/100\n\n{evaluation.get('feedback', '')}"
            missing = evaluation.get('missing_concepts', [])
            if missing:
                feedback += "\n\n**Improve:**\n" + "\n".join(f"- {concept}" for concept in missing)
            add_message("assistant", feedback)

            current_index += 1
            st.session_state.current_question_index = current_index

            if current_index < len(st.session_state.questions):
                next_question = st.session_state.questions[current_index]["question"]
                add_message("assistant", f"{random.choice(QUESTION_TRANSITIONS)}\n\n**Question {current_index + 1}:** {next_question}")
            else:
                st.session_state.bot_state = "complete"
                st.session_state.interview_complete = True
                evaluations = st.session_state.evaluations
                total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
                avg_score = total_score / len(evaluations) if evaluations else 0
                rating = "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement"

                interview_record = {
                    "candidate_name": st.session_state.candidate_name or "Candidate",
                    "date": st.session_state.interview_date,
                    "avg_score": avg_score,
                    "rating": rating,
                    "skills": st.session_state.skills,
                    "questions": st.session_state.questions,
                    "evaluations": st.session_state.evaluations
                }
                st.session_state.interview_history.append(interview_record)

                add_message("assistant", f"""
                ## Interview Complete!
                **Overall Score:** {avg_score:.1f}/100
                **Rating:** {rating}
                Options:
                1. Review answers
                2. Export PDF
                3. Send results via email
                4. View history
                5. Start new interview
                """)

        elif st.session_state.bot_state == "complete":
            if "review" in user_input.lower() or "answers" in user_input.lower():
                review = "## Your Responses\n\n"
                for i, q in enumerate(st.session_state.questions):
                    if q['question'] in st.session_state.evaluations:
                        data = st.session_state.evaluations[q['question']]
                        evaluation = data["evaluation"]
                        review += f"### Question {i+1}: {q['question']}\n"
                        review += f"**Answer:** {data['answer']}\n"
                        review += f"**Score:** {evaluation.get('score', 0)}/100\n"
                        review += f"**Feedback:** {evaluation.get('feedback', 'No feedback')}\n"
                        missing = evaluation.get('missing_concepts', [])
                        if missing:
                            review += "**Improve:**\n" + "\n".join(f"- {concept}" for concept in missing)
                        review += "\n---\n"
                add_message("assistant", review)

            elif "pdf" in user_input.lower() or "export" in user_input.lower():
                try:
                    evaluations = st.session_state.evaluations
                    total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
                    avg_score = total_score / len(evaluations) if evaluations else 0
                    interview_record = {
                        "candidate_name": st.session_state.candidate_name or "Candidate",
                        "date": st.session_state.interview_date,
                        "avg_score": avg_score,
                        "rating": "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement",
                        "skills": st.session_state.skills,
                        "questions": st.session_state.questions,
                        "evaluations": st.session_state.evaluations
                    }
                    pdf_path = export_results_as_pdf(interview_record)
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    pdf_b64 = base64.b64encode(pdf_bytes).decode()
                    add_message("assistant", f"PDF ready! <a href='data:application/pdf;base64,{pdf_b64}' download='{os.path.basename(pdf_path)}'>Download</a>")
                except Exception as e:
                    add_message("assistant", f"PDF generation error: {e}")

            elif "email" in user_input.lower() or "send" in user_input.lower():
                if st.session_state.user_email:
                    try:
                        evaluations = st.session_state.evaluations
                        total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
                        avg_score = total_score / len(evaluations) if evaluations else 0
                        interview_record = {
                            "candidate_name": st.session_state.candidate_name or "Candidate",
                            "date": st.session_state.interview_date,
                            "avg_score": avg_score,
                            "rating": "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement",
                            "skills": st.session_state.skills,
                            "questions": st.session_state.questions,
                            "evaluations": st.session_state.evaluations
                        }
                        pdf_path = export_results_as_pdf(interview_record)
                        if send_email(st.session_state.user_email, interview_record, pdf_path):
                            add_message("assistant", f"Results sent to {st.session_state.user_email}!")
                        else:
                            add_message("assistant", "Failed to send email. Try downloading the PDF.")
                    except Exception as e:
                        add_message("assistant", f"Error: {e}")
                else:
                    add_message("assistant", "No email available. Please log in again.")

            elif "history" in user_input.lower() or "past" in user_input.lower():
                if not st.session_state.interview_history:
                    add_message("assistant", "No past interviews. Complete one to build history!")
                else:
                    history_message = "## Interview History\n\n"
                    for idx, record in enumerate(st.session_state.interview_history):
                        history_message += f"### Interview {idx+1}: {record['candidate_name']} ({record['date']})\n"
                        history_message += f"**Score:** {record['avg_score']:.1f}/100\n"
                        history_message += f"**Rating:** {record['rating']}\n"
                        history_message += "**Skills:**\n"
                        for category, skills in record['skills'].items():
                            history_message += f"- {category.capitalize()}: {', '.join(skills)}\n"
                        history_message += "**Questions:**\n"
                        for i, q in enumerate(record['questions']):
                            if q['question'] in record['evaluations']:
                                eval_data = record['evaluations'][q['question']]
                                history_message += f"- Q{i+1}: {q['question']}\n"
                                history_message += f"  - **Answer:** {eval_data['answer']}\n"
                                history_message += f"  - **Score:** {eval_data['evaluation'].get('score', 0)}/100\n"
                        history_message += "\n---\n"
                    add_message("assistant", history_message)

            elif "new" in user_input.lower() or "start" in user_input.lower():
                initialize_session_state()
                st.rerun()
            else:
                add_message("assistant", """
                What's next?
                1. Review answers
                2. Export PDF
                3. Send results via email
                4. View history
                5. Start new interview
                """)

    # Handle file upload
    if uploaded_file is not None and not st.session_state.resume_text:
        from utils import extract_skills
        file_extension = uploaded_file.name.split(".")[-1].lower()
        if file_extension == "pdf":
            resume_text = extract_text_from_pdf(uploaded_file)
        elif file_extension == "docx":
            resume_text = extract_text_from_docx(uploaded_file)
        else:
            resume_text = ""
            st.error("Please upload a PDF or DOCX file.")

        if resume_text:
            st.session_state.resume_text = resume_text
            st.session_state.bot_state = "analyzing_resume"
            st.session_state.chat_messages = [{"role": "assistant", "content": "Analyzing your resume..."}]
            skills = extract_skills(resume_text)
            if not skills:
                add_message("assistant", "No skills found. List some skills (e.g., Python, Java, AWS).")
                st.session_state.bot_state = "manual_skills"
            else:
                st.session_state.skills = skills
                skill_message = random.choice(SKILL_MESSAGES) + "\n\n" + format_skills_message(skills)
                if st.session_state.debug_skills:
                    skill_message += "\n\n**Debug:**\n" + "\n".join(st.session_state.debug_skills)
                skill_message += "\n\nCorrect? Add skills or type 'start interview'."
                add_message("assistant", skill_message)
                st.session_state.bot_state = "confirm_skills"

    # Chat interface
    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"], unsafe_allow_html=True)

        if user_input := st.chat_input("Type here"):
            process_user_input(user_input)
            st.rerun()

    # Export on completion
    if st.session_state.interview_complete:
        with st.sidebar:
            st.subheader("Export")
            evaluations = st.session_state.evaluations
            total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
            avg_score = total_score / len(evaluations) if evaluations else 0
            if st.button("Generate PDF"):
                try:
                    interview_record = {
                        "candidate_name": st.session_state.candidate_name or "Candidate",
                        "date": st.session_state.interview_date,
                        "avg_score": avg_score,
                        "rating": "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement",
                        "skills": st.session_state.skills,
                        "questions": st.session_state.questions,
                        "evaluations": st.session_state.evaluations
                    }
                    pdf_path = export_results_as_pdf(interview_record)
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    pdf_b64 = base64.b64encode(pdf_bytes).decode()
                    st.markdown(f'<a href="data:application/pdf;base64,{pdf_b64}" download="{os.path.basename(pdf_path)}">Download PDF</a>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"PDF generation error: {e}")

            st.subheader("Send Results")
            if st.button("Send Email"):
                if st.session_state.user_email:
                    try:
                        evaluations = st.session_state.evaluations
                        total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
                        avg_score = total_score / len(evaluations) if evaluations else 0
                        interview_record = {
                            "candidate_name": st.session_state.candidate_name or "Candidate",
                            "date": st.session_state.interview_date,
                            "avg_score": avg_score,
                            "rating": "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement",
                            "skills": st.session_state.skills,
                            "questions": st.session_state.questions,
                            "evaluations": st.session_state.evaluations
                        }
                        pdf_path = export_results_as_pdf(interview_record)
                        if send_email(st.session_state.user_email, interview_record, pdf_path):
                            st.success(f"Results sent to {st.session_state.user_email}!")
                        else:
                            st.error("Failed to send email. Try downloading the PDF.")
                    except Exception as e:
                        st.error(f"Email error: {e}")
                else:
                    st.error("No email available. Please log in again.")

if __name__ == "__main__":
    main()