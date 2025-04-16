
# Firebase configuration
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyDvFFLr-Fjhma2yae7rx3r7Ei0J6bXJmmI",
    "authDomain": "client-2bbfc.firebaseapp.com",
    "databaseURL": "https://client-2bbfc-default-rtdb.firebaseio.com",
    "projectId": "client-2bbfc",
    "storageBucket": "client-2bbfc.firebasestorage.app",
    "messagingSenderId": "971318119261",
    "appId": "1:971318119261:web:0cf9b5f290f1589326f6b4",
    "measurementId": "G-5YHQGXBXJG"
}

# Email configuration
EMAIL_SENDER = "projecttestingsubhash@gmail.com"
EMAIL_PASSWORD = "zgwynxksfnwzusyk"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Skill definitions
COMMON_SKILLS = {
    'programming': ['python', 'java', 'javascript', 'html', 'css', 'c++', 'c#', 'ruby', 'php', 'sql'],
    'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node.js', 'express', '.net'],
    'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'sqlite', 'redis'],
    'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
    'tools': ['git', 'github', 'jira', 'jenkins', 'agile', 'scrum'],
}

# Load questions from CSV
def get_questions_from_csv(file_path):
    import csv
    from collections import defaultdict

    technical_questions = defaultdict(list)
    generic_questions = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                skill = row['skill'].lower()
                question = row['question']
                expected_keywords = row['expected_keywords'].split(',')

                question_data = {
                    "question": question,
                    "expected_keywords": expected_keywords
                }

                if skill == 'generic':
                    generic_questions.append(question_data)
                else:
                    technical_questions[skill].append(question_data)

        return dict(technical_questions), generic_questions

    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return {}, []
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return {}, []

# Load questions
TECHNICAL_QUESTIONS, GENERIC_QUESTIONS = get_questions_from_csv('questions.csv')

# Messages
WELCOME_MESSAGES = [
    "Welcome to TechInterviewBot! Let's practice your technical skills.",
    "Hello! Ready for a technical interview? I'm here to help.",
    "Hi! Let's sharpen your interview skills with tailored questions.",
]

RESUME_PROMPTS = [
    "Upload your resume or paste its content to start.",
    "Share your resume to tailor the interview questions.",
    "I need your resume to generate relevant questions.",
]

SKILL_MESSAGES = [
    "Great! Here are the skills I found in your resume:",
    "Thanks! I've identified these skills from your resume:",
    "Based on your resume, here are your key skills:",
]

INTERVIEW_START_MESSAGES = [
    "Let's start with questions based on your skills!",
    "Ready? Here come some technical questions!",
    "The interview begins with tailored questions.",
]

QUESTION_TRANSITIONS = [
    "Next question:",
    "Here's another one:",
    "Moving on:",
]

EVALUATION_POSITIVE = [
    "Great answer! You hit the key points.",
    "Excellent! Your response was clear and accurate.",
    "Well done! That was a strong answer.",
]

EVALUATION_AVERAGE = [
    "Good try! You covered some points, but there's room to grow.",
    "Decent answer, but you could add more detail.",
    "Not bad! Try expanding on the concepts.",
]

EVALUATION_NEEDS_IMPROVEMENT = [
    "You missed some key concepts. Let's review those.",
    "Needs more depth. Want some pointers?",
    "Try including more technical details.",
]