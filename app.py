import streamlit as st
import pandas as pd
import re
from datetime import datetime
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="WhatsApp Analyzer", layout="wide")

# --- CUSTOM CSS FOR WRAPPED STYLE ---
st.markdown("""
<style>
    .wrapped-box {
        background-color: #d4af37;
        padding: 20px;
        border-radius: 10px;
        color: black;
        text-align: center;
        margin-bottom: 20px;
    }
    .wrapped-title {
        font-size: 40px;
        font-weight: bold;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- PASSWORD LOGIC ---
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
    st.title("📊 WhatsApp Chat Insights")
    
    uploaded_file = st.file_uploader("Upload Chat .txt", type="txt")

    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8")
        lines = content.split('\n')
        
        data = []
        pattern = r'^\[(\d{2}/\d{2}/\d{4}),\s+(\d{2}:\d{2}:\d{2})\]\s+(.*?):\s+(.*)$'

        for line in lines:
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                date_str, time_str, author, message = match.groups()
                if "omitted" in message or "security code changed" in message:
                    continue
                dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S")
                data.append([dt, author, message])
        
        if data:
            df = pd.DataFrame(data, columns=['date', 'author', 'message'])
            df['year'] = df['date'].dt.year
            df['month_name'] = df['date'].dt.strftime('%B')
            
            # --- 2025 WRAPPED ---
            df_2025 = df[df['year'] == 2025]
            if not df_2025.empty:
                st.markdown('<div class="wrapped-box"><p class="wrapped-title">🎁 2025 WRAPPED</p>', unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                top_sender = df_2025['author'].value_counts().idxmax()
                msg_count = df_2025['author'].value_counts().max()
                busiest_month
