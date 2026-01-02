import streamlit as st
import pandas as pd
import re
from datetime import datetime
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="WhatsApp Analyzer", layout="wide")

# --- CUSTOM CSS FOR "WRAPPED" STYLE ---
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
    .wrapped-stat {
        font-size: 24px;
        margin: 5px;
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
        # Pattern for: [05/07/2018, 21:00:50] Name: Message
        pattern = r'^\[(\d{2}/\d{2}/\d{4}),\s+(\d{2}:\d{2}:\d{2})\]\s+(.*?):\s+(.*)$'

        for line in lines:
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                date_str, time_str, author, message = match.groups()
                # Skip system messages
                if "omitted" in message or "security code changed" in message:
                    continue
                dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S")
                data.append([dt, author, message])
        
        if data:
            df = pd.DataFrame(data, columns=['date', 'author', 'message'])
            df['year'] = df['date'].dt.year
            df['month_name'] = df['date'].dt.strftime('%B')
            
            # --- 🎁 2025 WRAPPED SECTION ---
            df_2025 = df[df['year'] == 2025]
            
            if not df_2025.empty:
                st.markdown('<div class="wrapped-box">', unsafe_allow_html=True)
                st.markdown('<p class="wrapped-title">🎁 2025 WRAPPED</p>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                # 1. The Champion
                top_sender = df_2025['author'].value_counts().idxmax()
                msg_count = df_2025['author'].value_counts().max()
                
                # 2. Busiest Month
                busiest_month = df_2025['month_name'].value_counts().idxmax()
                
                with col1:
                     st.metric("🏆 2025 Champion", top_sender, f"{msg_count} msgs")
                with col2:
                     st.metric("📅 Peak Month", busiest_month)
                with col3:
                     st.metric("💬 Total Messages", len(df_2025))
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()

            # --- REGULAR STATS ---
            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader("🏆 All-Time Chatterbox")
                st.bar_chart(df['author'].value_counts().head(10))

            with col_right:
                st.subheader("📅 Activity Over Time")
                df['date_only'] = df['date'].dt.date
                st.line_chart(df.groupby('date_only').count()['message'])

            # --- IMPROVED WORD CLOUD ---
            st.divider()
            st.subheader("☁️ The Vibe Check (Word Cloud)")
            
            text = " ".join(msg for msg in df['message'])
            
            # EXTENDED Stopwords List
            custom_stopwords = {
                "the", "and", "is", "to", "in", "it", "of", "for", "on", "that", "this", "my", "you", "are", 
                "be", "have", "with", "was", "at", "so", "but", "if", "or", "not", "just", "like", "can",
                "do", "we", "he", "she", "they", "them", "there", "then", "now", "go", "get", "got", "up", "out",
                "one", "about", "what", "when", "how", "know", "think", "see", "look", "good", "
