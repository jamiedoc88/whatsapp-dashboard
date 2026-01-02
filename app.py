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
        # Regex Pattern matches: [05/07/2018, 21:00:50] Name: Message
        pattern = r'^\[(\d{2}/\d{2}/\d{4}),\s+(\d{2}:\d{2}:\d{2})\]\s+(.*?):\s+(.*)$'

        for line in lines:
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                date_s, time_s, auth, msg = match.groups()
                # Filter system messages
                if "omitted" in msg or "security code" in msg:
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
            years_list = sorted(df['year'].unique(), reverse=True)
            selected_years = st.sidebar.multiselect("📅 Select Years", years_list, default=years_list)
            
            authors_list = sorted(df['author'].unique())
            selected_authors = st.sidebar.multiselect("👥 Select People", authors_list, default=authors_list)

            # Apply Filters (use .copy() to prevent silent errors)
            filtered_df = df[df['year'].isin(selected_years)]
            filtered_df = filtered_df[filtered_df['author'].isin(selected_authors)].copy()

            if filtered_df.empty:
                st.warning("No messages match your filters!")
            else:
                # --- SNAPSHOT METRICS ---
                st.markdown("### 📈 Snapshot")
                
                # Calculation Block (Wrapped in try/except to prevent crashing)
                try:
                    total_msgs = int(len(filtered_df))
                    active_days = int(filtered_df['date'].dt.date.nunique())
                    top_person = str(filtered_df['author'].value_counts().idxmax())
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Messages", total_msgs)
                    c2.metric("Active Days", active_days)
                    c3.metric("Top Chatter", top_person)
                except Exception as e:
                    st.error(f"Error calculating metrics: {e}")

                st.divider()

                # --- CHARTS ---
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.subheader("🏆 Leaderboard")
                    counts = filtered_df['author'].value_counts().head(15)
                    st.bar_chart(counts)

                with col_right:
                    st.subheader("📅 Activity Trend")
                    # Group by Month
                    df_trend = filtered_df.copy()
                    df_trend['month_year'] = df_trend['date'].dt.to_period('M').astype(str)
                    timeline = df_trend.groupby('month_year').size()
                    st.line_chart(timeline)

                # --- SEARCH ENGINE ---
                st.divider()
                st.subheader("🔎 The Detective")
                
                s_col1, s_col2 = st.columns([2, 1])
                with s_col1:
                    query = st.text_input("Search for (e.g. 'Rangers')")
                with s_col2:
                    opts = ["All"] + list(authors_list)
                    target_person = st.selectbox("Filter by Person", opts)
                
                if query:
                    mask = filtered_df['message'].str.contains(query, case=False, na=False)
                    if target_person != "All":
                        mask = mask & (filtered_df['author'] == target_person)
                    
                    results = filtered_df[mask]
                    st.success(f"Found **{len(results)}** mentions!")
                    
                    if not results.empty:
                        with st.expander("View Messages"):
                            st.dataframe(results[['date','author','message']].sort_values('date', ascending=False))

                # --- WORD CLOUD ---
                st.divider()
                st.subheader("☁️ Word Cloud")
                
                # Robust Text Block
                stop_text = """
                the and is to in it of for on that this my you are be have with was at so but if or not just like can do
                we he she they them there then now go get got up out one about what when how know think see look good well
                time day year people would could should really will going from don ll ve re wa ha m s t d
                lol haha omitted image video sticker GIF edited mate man guy boy aye ye u ur ok okay yeah nah
                shite fuck fucking wee cunt bit
                """
                custom_stopwords = set(stop_text.split())
                all_text = " ".join(msg for msg in filtered_df['message'])
                
                if len(all_text) > 0:
                    wc = WordCloud(width=1000, height=500, background_color='white', stopwords=custom_stopwords, min_word_length=3)
                    wc.generate(all_text)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis("off")
                    st.pyplot(fig)

    else:
        st.info("👈 Upload your file in the sidebar!")
