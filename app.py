import streamlit as st
import pandas as pd
import re
from datetime import datetime
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="WhatsApp Analyzer", layout="wide")

# --- CUSTOM STYLING ---
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
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
    
    # --- SIDEBAR: GLOBAL CONFIGURATION ---
    st.sidebar.header("⚙️ Configuration")
    uploaded_file = st.sidebar.file_uploader("Upload Chat .txt", type="txt")

    if uploaded_file is not None:
        # --- DATA PROCESSING ---
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
                try:
                    dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S")
                    data.append([dt, author, message])
                except ValueError:
                    continue
        
        if data:
            df = pd.DataFrame(data, columns=['date', 'author', 'message'])
            df['year'] = df['date'].dt.year
            df['month_name'] = df['date'].dt.strftime('%B')
            
            # --- SIDEBAR FILTERS ---
            all_years = sorted(df['year'].unique(), reverse=True)
            selected_years = st.sidebar.multiselect("📅 Select Years", all_years, default=all_years)
            
            all_authors = sorted(df['author'].unique())
            selected_authors = st.sidebar.multiselect("👥 Select People", all_authors, default=all_authors)

            # --- FILTER THE DATA ---
            filtered_df = df[
                (df['year'].isin(selected_years)) & 
                (df['author'].isin(selected_authors))
            ]

            if filtered_df.empty:
                st.warning("No messages match your filters!")
            else:
                # --- MAIN DASHBOARD ---
                
                # 1. METRICS
                st.markdown("### 📈 Snapshot")
                c1, c2, c3 = st.columns(3)
                c1.metric("Messages", len(filtered_df))
                c2.metric("Active Days", filtered_df['date'].dt.date.nunique())
                
                # Top Chatter in selection
                if not filtered_df.empty:
                    top_person = filtered_df['author'].value_counts().idxmax()
                    c3.metric("Top Chatter", top_person)

                st.divider()

                # 2. CHARTS
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.subheader("🏆 Leaderboard")
                    st.bar_chart(filtered_df['author'].value_counts().
