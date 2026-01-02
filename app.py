import streamlit as st
import pandas as pd
import re
from datetime import datetime

# --- PASSWORD PROTECTION ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if check_password():
    st.title("WhatsApp Analyzer (Debug Mode) 🇬🇧")
    
    uploaded_file = st.file_uploader("Upload Chat .txt", type="txt")

    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8")
        lines = content.split('\n')
        
        data = []
        
        # PATTERN 1: iOS UK ([14/06/2023, 15:00:00] Author: Message)
        ios_pattern = r'^\[(\d{2}/\d{2}/\d{4}),\s+(\d{2}:\d{2}:\d{2})\]\s+([^:]+):\s+(.*)'
        
        # PATTERN 2: Android UK (14/06/2023, 15:00 - Author: Message)
        android_pattern = r'^(\d{2}/\d{2}/\d{4}),\s+(\d{2}:\d{2})\s+-\s+([^:]+):\s+(.*)'

        for line in lines:
            line = line.strip()
            # Try iOS match
            match = re.match(ios_pattern, line)
            if match:
                date, time, author, msg = match.groups()
                dt = datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M:%S")
                data.append([dt, author, msg])
                continue # Skip to next line
            
            # Try Android match
            match = re.match(android_pattern, line)
            if match:
                date, time, author, msg = match.groups()
                dt = datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M")
                data.append([dt, author, msg])
                continue

        # --- THE RESULT ---
        if len(data) > 0:
            df = pd.DataFrame(data, columns=['date', 'author', 'message'])
            st.success(f"Success! Analyzed {len(df)} messages.")
            
            # Charts
            st.subheader("Messages per Person")
            st.bar_chart(df['author'].value_counts())
            
            st.subheader("Activity Over Time")
            df['date_only'] = df['date'].dt.date
            st.line_chart(df.groupby('date_only').count()['message'])
            
        else:
            # --- DEBUGGER: SHOW ME THE DATA ---
            st.error("Still could not parse the file. Here is what your text looks like:")
            st.write("Please copy the lines below and paste them into Gemini:")
            st.code("\n".join(lines[:5]))
