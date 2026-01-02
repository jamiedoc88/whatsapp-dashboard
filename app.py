import streamlit as st
import pandas as pd
import re
from datetime import datetime
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# --- PAGE CONFIG ---
st.set_page_config(page_title="WhatsApp Analyzer", layout="wide")

# --- CUSTOM CSS ---
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
</style>
""", unsafe_allow_html=True)

# --- PASSWORD CHECK ---
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
    
    # --- SIDEBAR START ---
    st.sidebar.header("⚙️ Configuration")
    uploaded_file = st.sidebar.file_uploader("Upload Chat .txt", type="txt")

    if uploaded_file is not None:
        # Read file
        content = uploaded_file.getvalue().decode("utf-8")
        lines = content.split('\n')
        
        data = []
        # Regex Pattern
        pattern = r'^\[(\d{2}/\d{2}/\d{4}),\s+(\d{2}:\d{2}:\d{2})\]\s+(.*?):\s+(.*)$'

        for line in lines:
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                date_s, time_s, auth, msg = match.groups()
                
                # Filter system messages
                if "omitted" in msg:
                    continue
                if "security code" in msg:
                    continue
                    
                try:
                    full_date = f"{date_s} {time_s}"
                    dt = datetime.strptime(full_date, "%d/%m/%Y %H:%M:%S")
                    data.append([dt, auth, msg])
                except ValueError:
                    continue
        
        if data:
            # Create DataFrame
            df = pd.DataFrame(data, columns=['date', 'author', 'message'])
            df['year'] = df['date'].dt.year
            
            # --- FILTERS ---
            # Get list of unique years
            years_list = sorted(df['year'].unique(), reverse=True)
            
            # Sidebar: Year Selector
            selected_years = st.sidebar.multiselect(
                "📅 Select Years", 
                years_list, 
                default=years_list
            )
            
            # Sidebar: Author Selector
            authors_list = sorted(df['author'].unique())
            selected_authors = st.sidebar.multiselect(
                "👥 Select People", 
                authors_list, 
                default=authors_list
            )

            # Apply Filters
            filtered_df = df[df['year'].isin(selected_years)]
            filtered_df = filtered_df[filtered_df['author'].isin(selected_authors)]

            if filtered_df.empty:
                st.warning("No messages match your filters!")
            else:
                # --- SNAPSHOT METRICS ---
                st.markdown("### 📈 Snapshot")
                c1, c2, c3 = st.columns(3)
                
                # Metric 1
