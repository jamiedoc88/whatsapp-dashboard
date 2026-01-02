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

# --- CACHED DATA LOADER (SPEED BOOST) ---
@st.cache_data(show_spinner="Parsing chat history...")
def load_and_parse_data(file_content):
    """
    Reads the file only ONCE. Subsequent runs use the cached memory.
    """
    lines = file_content.decode("utf-8").split('\n')
    data = []
    # Regex: [05/07/2018, 21:00:50] Name: Message
    pattern = r'^\[(\d{2}/\d{2}/\d{4}),\s+(\d{2}:\d{2}:\d{2})\]\s+(.*?):\s+(.*)$'

    for line in lines:
        line = line.strip()
        match = re.match(pattern, line)
        if match:
            date_s, time_s, auth, msg = match.groups()
            
            if "omitted" in msg or "security code" in msg:
                continue
                
            try:
                full_date = f"{date_s} {time_s}"
                dt = datetime.strptime(full_date, "%d/%m/%Y %H:%M:%S")
                data.append([dt, auth, msg])
            except ValueError:
                continue
    
    if data:
        df = pd.DataFrame(data, columns=['date', 'author', 'message'])
        df['year'] = df['date'].dt.year
        return df
    return pd.DataFrame()

# --- MAIN APP ---
if check_password():
    st.title("📊 WhatsApp Chat Insights")
    
    st.sidebar.header("⚙️ Configuration")
    uploaded_file = st.sidebar.file_uploader("Upload Chat .txt", type="txt")

    if uploaded_file is not None:
        # 1. LOAD DATA (Uses Cache)
        df = load_and_parse_data(uploaded_file.getvalue())
        
        if df.empty:
            st.error("Could not parse file. Check format.")
        else:
            # --- FILTERS ---
            years_list = sorted(df['year'].unique(), reverse=True)
            selected_years = st.sidebar.multiselect("📅 Select Years", years_list, default=years_list)
            
            authors_list = sorted(df['author'].unique())
            selected_authors = st.sidebar.multiselect("👥 Select People", authors_list, default=authors_list)

            # Apply Filters
            filtered_df = df[df['year'].isin(selected_years)]
            filtered_df = filtered_df[filtered_df['author'].isin(selected_authors)].copy()

            if filtered_df.empty:
                st.warning("No messages match your filters!")
            else:
                # --- SNAPSHOT ---
                st.markdown("### 📈 Snapshot")
                try:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Messages", int(len(filtered_df)))
                    c2.metric("Active Days", int(filtered_df['date'].dt.date.nunique()))
                    c3.metric("Top Chatter", str(filtered_df['author'].value_counts().idxmax()))
                except Exception:
                    st.write("Metric calculation error")

                st.divider()

                # --- CHARTS ---
                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("🏆 Leaderboard")
                    st.bar_chart(filtered_df['author'].value_counts().head(15))

                with col_right:
                    st.subheader("📅 Activity Trend")
                    df_trend = filtered_df.copy()
                    df_trend['month_year'] = df_trend['date'].dt.to_period('M').astype(str)
                    st.line_chart(df_trend.groupby('month_year').size())

                # --- SEARCH ENGINE (IMPROVED) ---
                st.divider()
                st.subheader("🔎 The Detective")
                
                s_col1, s_col2 = st.columns([2, 1])
                with s_col1:
                    query = st.text_input("Search for (e.g. 'Rangers')")
                with s_col2:
                    target_person = st.selectbox("Filter by Person", ["All"] + list(authors_list))
                
                if query:
                    # Case-insensitive search
                    mask = filtered_df['message'].str.contains(query, case=False, na=False)
                    if target_person != "All":
                        mask = mask & (filtered_df['author'] == target_person)
                    
                    results = filtered_df[mask]
                    
                    st.success(f"Found **{len(results)}** mentions of '{query}'!")
                    
                    if not results.empty:
                        # NEW: Who said it most table?
                        st.write(f"**Who mentions '{query}' the most?**")
                        
                        # Create a clean frequency table
                        freq_table = results['author'].value_counts().reset_index()
                        freq
