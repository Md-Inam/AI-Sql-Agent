import os
import pandas as pd
from sqlalchemy import create_engine
from langchain.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI as GenAI
from langchain_community.agent_toolkits import create_sql_agent
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit UI Layout
st.set_page_config(layout="wide")  # Make layout wider

# Sidebar: Gemini API Key Input (Top Left)
st.sidebar.title("🔑 Enter Gemini API Key")
google_api_key = st.sidebar.text_input("API Key", type="password")

# Sidebar: File Upload
st.sidebar.title("📂 Upload File")
uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

if google_api_key and uploaded_file:
    os.environ["GOOGLE_API_KEY"] = google_api_key  # Set API Key

    # Load the dataset
    file_ext = uploaded_file.name.split(".")[-1]
    
    if file_ext == "csv":
        df = pd.read_csv(uploaded_file)
    elif file_ext == "xlsx":
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    
    # Create SQLite database
    engine = create_engine("sqlite:///uploaded_data.db")
    df.to_sql("uploaded_table", engine, index=False, if_exists='replace')

    # Initialize SQL database
    db = SQLDatabase(engine=engine)

    # Initialize AI Model
    llm = GenAI(model="gemini-1.5-flash", temperature=0, google_api_key=os.environ["GOOGLE_API_KEY"])

    # Create Text-to-SQL Agent
    agent_executor = create_sql_agent(llm, db=db, verbose=True, return_intermediate_steps=True)

    # Center Layout
    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        st.title("🤖 AI Agent Text-to-SQL")
        query = st.text_input("Enter your query:")

        if query:
            response = agent_executor.run(query)
            st.write("### SQL Query Result:")
            st.write(response)

elif not google_api_key:
    st.sidebar.warning("⚠️ Please enter your Gemini API Key.")

elif not uploaded_file:
    st.sidebar.info("📂 Upload a file to get started.")

