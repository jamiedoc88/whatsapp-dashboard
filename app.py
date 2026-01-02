import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="WhatsApp Chat Analyzer", layout="wide")

# --- 1. Password Protection ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # Initialize session state for password
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # Return True if already authenticated
    if st.session_state["password_correct"]:
        return True

    # Show input for password
    st.text_input(
        "Enter Password", type="password", on_change=password_entered, key="password"
    )
    
    if "password_correct" in st.session_state and st.session_state["password_correct"] == False:
        st.error("😕 Password incorrect")

    return False

# Stop execution if password is not correct
if not check_password():
    st.stop()

# --- 2. Main App Interface ---
st.title("📱 WhatsApp Chat Analyzer")
st.markdown("Upload your exported WhatsApp `.txt` file to visualize the data.")

# --- 3. File Uploader ---
uploaded_file = st.file_uploader("Choose a WhatsApp Chat .txt file", type="txt")

# --- 4. The Analysis Logic ---
@st.cache_data
def parse_chat(file):
    """
    Parses WhatsApp chat log.
    Regex handles format: "dd/mm/yy, hh:mm - Author: Message"
    """
    data = []
    # Decode bytes to string
    string_data = file.getvalue().decode("utf-8")
    lines = string_data.split('\n')
    
    # Regex pattern for "date, time - Author: Message"
    # Note: WhatsApp formats vary by region/device. This is the standard Android/iOS export format.
    pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}) - ([^:]+): (.+)$'
    
    for line in lines:
        match = re.match(pattern, line)
        if match:
            date_time_str, author, message = match.groups()
            data.append([date_time_str, author, message])
    
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data, columns=["DateTime", "Author", "Message"])
    
    # Convert DateTime column to datetime objects
    # Errors='coerce' will handle format mismatches gracefully
    df['DateTime'] = pd.to_datetime(df['DateTime'], format='%d/%m/%y, %H:%M', errors='coerce')
    
    # If the default format failed (e.g. year is YYYY instead of YY), try flexible parsing
    if df['DateTime'].isnull().all():
         df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')

    return df.dropna()

if uploaded_file is not None:
    # Process Data
    df = parse_chat(uploaded_file)

    if df.empty:
        st.error("Could not parse the file. Please ensure it is a standard WhatsApp export (dd/mm/yy format).")
    else:
        st.success(f"Successfully loaded {len(df)} messages!")

        # Layout Columns
        col1, col2 = st.columns(2)

        # --- 5. Visuals ---

        # Visual A: Messages per Person (Bar Chart)
        with col1:
            st.subheader("Messages per Person")
            author_counts = df['Author'].value_counts()
            
            # Using Matplotlib as requested
            fig_bar, ax_bar = plt.subplots()
            author_counts.plot(kind='bar', ax=ax_bar, color='skyblue', edgecolor='black')
            ax_bar.set_ylabel("Message Count")
            ax_bar.set_xlabel("Author")
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig_bar)

        # Visual B: Activity Over Time (Line Chart)
        with col2:
            st.subheader("Activity Over Time")
            # Group by Date
            df['Date'] = df['DateTime'].dt.date
            date_counts = df.groupby('Date').count()['Message']
            
            # Using Matplotlib as requested
            fig_line, ax_line = plt.subplots()
            date_counts.plot(kind='line', ax=ax_line, color='green', marker='o', markersize=3)
            ax_line.set_ylabel("Messages")
            ax_line.set_xlabel("Date")
            plt.xticks(rotation=45)
            st.pyplot(fig_line)

        # Show raw data (optional but helpful)
        with st.expander("View Raw Data"):
            st.dataframe(df)