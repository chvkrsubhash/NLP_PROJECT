# utils.py
import re
import random
from textblob import TextBlob, Word
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

from config import COMMON_SKILLS, TECHNICAL_QUESTIONS, GENERIC_QUESTIONS

# Text preprocessing
def preprocess_text(text):
    try:
        blob = TextBlob(text.lower())
        tokens = [Word(word).lemmatize() for word in blob.words if word.isalnum()]
        stop_words = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 
                      'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'}
        tokens = [t for t in tokens if t not in stop_words]
        return " ".join(tokens)
    except Exception:
        return text.lower()

# Skill extraction
def extract_skills(text):
    if not text:
        return {}
    
    try:
        raw_text = text.lower()
        blob = TextBlob(raw_text)
        identified_skills = {}
        debug_matches = []
        
        context_patterns = r'(?:skills|experience|proficient in|worked with|knowledge of|using|expertise in)'
        
        for category, skill_list in COMMON_SKILLS.items():
            found_skills = set()
            for skill in skill_list:
                pattern = rf'{context_patterns}\s*[^.\n]*\b{re.escape(skill)}\b[^.\n]*'
                matches = re.finditer(pattern, raw_text)
                for match in matches:
                    context = match.group()
                    if skill in [Word(w).lemmatize() for w in TextBlob(context).words]:
                        found_skills.add(skill)
                        debug_matches.append(f"Matched '{skill}' in: '{context[:50]}...'")
            if found_skills:
                identified_skills[category] = list(found_skills)
        
        st.session_state.debug_skills = debug_matches
        st.session_state.raw_resume_text = raw_text
        return identified_skills
    except Exception:
        identified_skills = {}
        for category, skill_list in COMMON_SKILLS.items():
            found_skills = set()
            for skill in skill_list:
                pattern = rf'{context_patterns}\s*[^.\n]*\b{re.escape(skill)}\b[^.\n]*'
                if re.search(pattern, text.lower()):
                    found_skills.add(skill)
            if found_skills:
                identified_skills[category] = list(found_skills)
        return identified_skills

# File processing
def extract_text_from_pdf(pdf_file):
    if PyPDF2 is None:
        return ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        return "".join(page.extract_text() or "" for page in pdf_reader.pages)
    except Exception:
        return ""

def extract_text_from_docx(docx_file):
    if docx is None:
        return ""
    try:
        doc = docx.Document(docx_file)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    except Exception:
        return ""

# Question generation
def generate_technical_questions(skills, max_questions=5):
    all_possible_questions = []
    all_skills = [skill for category, skill_list in skills.items() for skill in skill_list]
    
    selected_skills = random.sample(all_skills, min(len(all_skills), 3)) if all_skills else []
    
    for skill in selected_skills:
        if skill in TECHNICAL_QUESTIONS:
            all_possible_questions.extend(random.sample(TECHNICAL_QUESTIONS[skill], min(2, len(TECHNICAL_QUESTIONS[skill]))))
    
    remaining_slots = max_questions - len(all_possible_questions)
    if remaining_slots > 0:
        all_possible_questions.extend(random.sample(GENERIC_QUESTIONS, min(remaining_slots, len(GENERIC_QUESTIONS))))
        remaining_slots = max_questions - len(all_possible_questions)
    
    if remaining_slots > 0:
        other_questions = [q for skill in TECHNICAL_QUESTIONS if skill not in selected_skills for q in TECHNICAL_QUESTIONS[skill]]
        all_possible_questions.extend(random.sample(other_questions, min(remaining_slots, len(other_questions))))
    
    random.shuffle(all_possible_questions)
    
    unique_questions = []
    question_texts = set()
    for q in all_possible_questions:
        if q["question"] not in question_texts:
            unique_questions.append(q)
            question_texts.add(q["question"])
    
    return unique_questions[:max_questions]

# Feedback formatting
def get_feedback_message(score):
    from config import EVALUATION_POSITIVE, EVALUATION_AVERAGE, EVALUATION_NEEDS_IMPROVEMENT
    if score >= 80:
        return random.choice(EVALUATION_POSITIVE)
    elif score >= 60:
        return random.choice(EVALUATION_AVERAGE)
    else:
        return random.choice(EVALUATION_NEEDS_IMPROVEMENT)

def format_skills_message(skills):
    return "\n".join(f"**{category.capitalize()}**: {', '.join(skill_list)}" for category, skill_list in skills.items())