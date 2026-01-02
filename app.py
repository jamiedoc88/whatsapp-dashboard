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

# --- CACHED DATA LOADER ---
@st.cache_data(show_spinner="Parsing chat history...")
def load_and_parse_data(file_content):
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
        # Load Data
        df = load_and_parse_data(uploaded_file.getvalue())
        
        if df.empty:
            st.error("Could not parse file. Check format.")
        else:
            # --- FILTERS ---
            years = sorted(df['year'].unique(), reverse=True)
            sel_years = st.sidebar.multiselect("📅 Select Years", years, default=years)
            
            authors = sorted(df['author'].unique())
            sel_authors = st.sidebar.multiselect("👥 Select People", authors, default=authors)

            # Apply Filters
            filtered_df = df[df['year'].isin(sel_years)]
            filtered_df = filtered_df[filtered_df['author'].isin(sel_authors)].copy()

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

                # --- SEARCH ENGINE ---
                st.divider()
                st.subheader("🔎 The Detective")
                
                s_col1, s_col2 = st.columns([2, 1])
                with s_col1:
                    query = st.text_input("Search for (e.g. 'Rangers')")
                with s_col2:
                    target = st.selectbox("Filter by Person", ["All"] + list(authors))
                
                if query:
                    mask = filtered_df['message'].str.contains(query, case=False, na=False)
                    if target != "All":
                        mask = mask & (filtered_df['author'] == target)
                    
                    results = filtered_df[mask]
                    st.success(f"Found **{len(results)}** mentions of '{query}'!")
                    
                    if not results.empty:
                        # Who said it most?
                        st.write(f"**Who mentions '{query}' the most?**")
                        
                        # Shorter variable names to prevent copy errors
                        counts = results['author'].value_counts()
                        stats = counts.reset_index()
                        stats.columns = ['Author', 'Mentions']
                        
                        r_c1, r_c2 = st.columns(2)
                        with r_c1:
                            st.dataframe(stats, hide_index=True, use_container_width=True)
                        with r_c2:
                            st.bar_chart(counts)
                        
                        with st.expander("View Messages"):
                            view = results[['date', 'author', 'message']]
                            st.dataframe(view.sort_values('date', ascending=False), use_container_width=True)

                # --- WORD CLOUD ---
                st.divider()
                st.subheader("☁️ Word Cloud")
                
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
        st.info("👈 Upload your file in the sidebar to start!")
