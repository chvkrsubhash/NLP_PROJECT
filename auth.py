# auth.py
import streamlit as st
import pyrebase
from config import FIREBASE_CONFIG

# Initialize Firebase
try:
    firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
    auth = firebase.auth()
except Exception as e:
    st.error(f"Firebase initialization failed: {e}. Check secrets.")
    auth = None

# Login function
def login():
    if "user" not in st.session_state or "user_email" not in st.session_state:
        st.session_state.user = None
        st.session_state.user_email = None
    
    if not st.session_state.user:
        st.title("Login to Technical Interview Chatbot")
        login_option = st.selectbox("Choose login method", ["Email/Password", "Sign Up"])
        
        if login_option == "Email/Password":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    st.session_state.user = user
                    st.session_state.user_email = user.get('email', None)
                    if not st.session_state.user_email:
                        st.error("No email found in user data. Please try again.")
                        return False
                    st.success("Logged in successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
        
        elif login_option == "Sign Up":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Sign Up"):
                try:
                    user = auth.create_user_with_email_and_password(email, password)
                    st.session_state.user = user
                    st.session_state.user_email = user.get('email', None)
                    if not st.session_state.user_email:
                        st.error("No email found in user data. Please try again.")
                        return False
                    st.success("Account created and logged in!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sign up failed: {e}")
        
        return False
    return True