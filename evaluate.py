# evaluate.py
import json
try:
    import google.generativeai as genai
except ImportError:
    genai = None
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils import preprocess_text

# Cosine similarity evaluation
def evaluate_with_cosine_similarity(answer, expected_keywords):
    try:
        # Preprocess answer and keywords
        processed_answer = preprocess_text(answer)
        keyword_text = " ".join(expected_keywords)
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([processed_answer, keyword_text])
        
        # Compute cosine similarity
        sim_score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
        
        # Convert similarity to a score (0-100)
        score = int(sim_score * 100)
        
        # Determine missing concepts
        answer_words = set(processed_answer.split())
        missing_concepts = [kw for kw in expected_keywords if kw not in answer_words]
        
        # Generate feedback
        if score >= 80:
            feedback = "Your answer covered most expected concepts well."
        elif score >= 60:
            feedback = "You addressed some key points, but could elaborate more."
        else:
            feedback = "Your answer missed several important concepts."
        
        if missing_concepts:
            feedback += f" Try including: {', '.join(missing_concepts)}."
        
        return {
            "score": score,
            "feedback": feedback,
            "missing_concepts": missing_concepts
        }
    except Exception as e:
        return {
            "score": 0,
            "feedback": f"Cosine similarity evaluation failed: {str(e)}",
            "missing_concepts": expected_keywords
        }

# Main evaluation function
def evaluate_answer(question, answer, expected_keywords):
    if not answer.strip():
        return {"score": 0, "feedback": "No answer provided.", "missing_concepts": expected_keywords}
    
    # Try Gemini API first
    if genai:
        try:
            genai.configure(api_key="AIzaSyDlb0thGyUHOBuT5bmv9a8QCkg-UX5iMgY")
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            You are a technical interviewer. Evaluate:
            **Question**: {question}
            **Answer**: {answer}
            **Expected Concepts**: {', '.join(expected_keywords)}
            Return JSON:
            {{"score": <0-100>, "feedback": "<string>", "missing_concepts": [<string>, ...]}}
            """
            response = model.generate_content(prompt)
            if response and hasattr(response, 'text') and response.text:
                result = json.loads(response.text.strip().replace("```json\n", "").replace("\n```", ""))
                score = min(max(result.get("score", 0), 0), 100)
                return {
                    "score": score,
                    "feedback": result.get("feedback", "No feedback."),
                    "missing_concepts": result.get("missing_concepts", [])
                }
            return evaluate_with_cosine_similarity(answer, expected_keywords)
        except Exception as e:
            return evaluate_with_cosine_similarity(answer, expected_keywords)
    else:
        return evaluate_with_cosine_similarity(answer, expected_keywords)