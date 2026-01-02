import streamlit as st
import pandas as pd
import re
from datetime import datetime
import matplotlib.pyplot as plt

# 1. PASSWORD PROTECTION
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    # 2. APP LOGIC STARTS HERE
    st.title("WhatsApp Chat Analyzer 🇬🇧")

    uploaded_file = st.file_uploader("Upload your WhatsApp Chat (.txt)", type="txt")

    if uploaded_file is not None:
        # Read the file
        content = uploaded_file.getvalue().decode("utf-8")
        lines = content.split('\n')
        
        # Lists to store data
        dates = []
        authors = []
        messages = []

        # Regex for UK Format: [14/06/2023, 10:00:00] or 14/06/2023, 10:00 - 
        # Tries to capture: Date, Time, Author, Message
        pattern = r'^\[?(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\]?\s+(?:- )?([^:]+): (.*)'

        for line in lines:
            match = re.match(pattern, line)
            if match:
                date_str, time_str, author, message = match.groups()
                # Force UK Date parsing (Day First)
                try:
                    full_date = f"{date_str} {time_str}"
                    # Try parsing with 4 digit year first, then 2 digit
                    try:
                        dt = datetime.strptime(full_date, '%d/%m/%Y %H:%M:%S')
                    except ValueError:
                         try:
                             dt = datetime.strptime(full_date, '%d/%m/%y %H:%M:%S')
                         except:
                             dt = datetime.strptime(full_date, '%d/%m/%Y %H:%M')
                    
                    dates.append(dt)
                    authors.append(author)
                    messages.append(message)
                except Exception as e:
                    continue # Skip lines that fail strictly

        # Create DataFrame
        if len(dates) == 0:
            st.error("Could not find any messages. Please check if your file is a standard export.")
        else:
            df = pd.DataFrame({'date': dates, 'author': authors, 'message': messages})
            
            # --- VISUALIZATIONS ---
            
            # 1. Total Stats
            st.metric("Total Messages", len(df))
            
            # 2. Messages per Person (Bar Chart)
            st.subheader("Who talks the most?")
            author_counts = df['author'].value_counts()
            st.bar_chart(author_counts)

            # 3. Activity Over Time (Line Chart)
            st.subheader("Activity Over Time")
            df['date_only'] = df['date'].dt.date
            daily_counts = df.groupby('date_only').count()['message']
            st.line_chart(daily_counts)
