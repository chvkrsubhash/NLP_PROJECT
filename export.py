# export.py# export.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF
import os
from datetime import datetime
from config import EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT

# Text sanitization for PDF
def sanitize_text(text):
    if not text:
        return ""
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"', '\u2013': '-', '\u2014': '--',
    }
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    return text.encode('ascii', 'ignore').decode('ascii')

# Email sending
def send_email(recipient_email, interview_record, pdf_path=None):
    if not recipient_email:
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = f"Technical Interview Results - {interview_record['candidate_name']}"
        
        avg_score = interview_record.get('avg_score', 0)
        rating = interview_record.get('rating', 'N/A')
        skills = ", ".join([f"{category}: {', '.join(skills)}" for category, skills in interview_record.get('skills', {}).items()])
        
        body = f"""
        Dear {interview_record['candidate_name']},
        
        Your technical interview is complete!
        
        Overall Score: {avg_score:.1f}/100
        Rating: {rating}
        Skills: {skills if skills else 'None identified'}
        
        See the attached PDF for details (if available).
        
        Thank you,
        TechInterviewBot
        """
        msg.attach(MIMEText(body, 'plain'))
        
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={os.path.basename(pdf_path)}'
            )
            msg.attach(part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception:
        return False

# PDF export
def export_results_as_pdf(interview_record):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Technical Interview Results", ln=True, align="C")
    pdf.ln(5)
    
    candidate_name = sanitize_text(interview_record.get("candidate_name", "Candidate"))
    interview_date = interview_record.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))
    evaluations = interview_record.get("evaluations", {})
    total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
    avg_score = total_score / len(evaluations) if evaluations else 0
    rating = "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement"
    skills = interview_record.get("skills", {})
    questions = interview_record.get("questions", [])
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Candidate: {candidate_name}", ln=True)
    pdf.cell(0, 10, f"Date: {interview_date}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Overall Score: {avg_score:.1f}/100", ln=True)
    pdf.cell(0, 10, f"Rating: {rating}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Skills", ln=True)
    pdf.set_font("Arial", "", 12)
    for category, skill_list in skills.items():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, category.capitalize(), ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, ", ".join(sanitize_text(skill) for skill in skill_list))
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Questions and Evaluations", ln=True)
    for i, q in enumerate(questions):
        if q['question'] in evaluations:
            data = evaluations[q['question']]
            evaluation = data["evaluation"]
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Question {i+1}: {sanitize_text(q['question'])}", ln=True)
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, f"Answer: {sanitize_text(data['answer'])}")
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Score: {evaluation.get('score', 0)}/100", ln=True)
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, f"Feedback: {sanitize_text(evaluation.get('feedback', 'No feedback'))}")
            missing = evaluation.get('missing_concepts', [])
            if missing:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Missing concepts:", ln=True)
                pdf.set_font("Arial", "", 12)
                for concept in missing:
                    pdf.cell(0, 10, f"- {sanitize_text(concept)}", ln=True)
            pdf.ln(5)
    
    output_path = f"interview_results_{candidate_name}_{interview_date.replace(':', '-')}.pdf"
    pdf.output(output_path)
    return output_path