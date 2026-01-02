import streamlit as st
import pandas as pd
import re
from datetime import datetime
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# --- PAGE CONFIGURATION (Make it look professional) ---
st.set_page_config(page_title="WhatsApp Analyzer", layout="wide")

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
    # --- APP HEADER ---
    st.title("📊 WhatsApp Chat Insights")
    st.markdown("Discover the hidden patterns in your group chat.")
    
    uploaded_file = st.file_uploader("Upload Chat .txt", type="txt")

    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8")
        lines = content.split('\n')
        
        data = []
        # The specific pattern that matches your file: [05/07/2018, 21:00:50] Name: Message
        pattern = r'^\[(\d{2}/\d{2}/\d{4}),\s+(\d{2}:\d{2}:\d{2})\]\s+(.*?):\s+(.*)$'

        for line in lines:
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                date_str, time_str, author, message = match.groups()
                dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S")
                data.append([dt, author, message])
        
        if data:
            df = pd.DataFrame(data, columns=['date', 'author', 'message'])
            
            # --- TOP METRICS ROW ---
            st.divider()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Messages", len(df))
            with col2:
                st.metric("Total Members", df['author'].nunique())
            with col3:
                # Calculate days active
                days = (df['date'].max() - df['date'].min()).days
                st.metric("Days Active", f"{days} days")
            st.divider()

            # --- TWO COLUMN LAYOUT ---
            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader("🏆 The Chatterbox Award")
                # Visual improvement: Horizontal bar chart is easier to read for names
                st.bar_chart(df['author'].value_counts())

            with col_right:
                st.subheader("📅 Activity Over Time")
                df['date_only'] = df['date'].dt.date
                st.line_chart(df.groupby('date_only').count()['message'])

            # --- WORD CLOUD SECTION ---
            st.divider()
            st.subheader("☁️ What do you talk about?")
            
            # 1. Combine all text
            text = " ".join(msg for msg in df['message'])
            
            # 2. Stopwords (Words to ignore) - You can add more here!
            stopwords = {"media", "omitted", "image", "video", "GIF", "sticker", "the", "and", "is", "to", "in", "it", "of", "for", "on", "that", "this", "my", "you", "are"}
            
            # 3. Generate the cloud
            if len(text) > 0:
                wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=stopwords).generate(text)
                
                # 4. Display it using Matplotlib
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)
            else:
                st.warning("Not enough text to generate a word cloud!")

        else:
            st.error("Could not parse file. The format seems different than expected.")
