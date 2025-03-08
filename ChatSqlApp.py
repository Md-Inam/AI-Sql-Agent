import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from langchain.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI as GenAI
from langchain_community.agent_toolkits import create_sql_agent

# Streamlit UI setup
st.set_page_config(layout="wide", page_title="AI SQL Agent")

# Sidebar for Gemini API Key
st.sidebar.title("🔑 Enter API Key")
api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

# File Uploader
st.sidebar.title("📂 Upload CSV File")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])

# Main layout
st.title("🤖 AI-Powered Text-to-SQL Converter")
st.write("Enter a natural language query, and the AI will generate the SQL command.")

# If API key and file are uploaded, process the file
if api_key and uploaded_file:
    os.environ["GOOGLE_API_KEY"] = api_key

    # Load CSV into DataFrame
    df = pd.read_csv(uploaded_file)

    # Create SQLite database
    engine = create_engine("sqlite:///uploaded_data.db")
    df.to_sql("uploaded_table", engine, index=False, if_exists='replace')

    # Initialize SQL database
    db = SQLDatabase(engine=engine)

    # Initialize AI Model
    llm = GenAI(model="gemini-1.5-flash", temperature=0, google_api_key=api_key)

    # Create SQL Agent
    agent_executor = create_sql_agent(llm, db=db, verbose=True, return_intermediate_steps=True)

    # Input query
    query = st.text_input("🔍 Enter your question:")

    if query:
        response = agent_executor.invoke({"input": query})
        sql_query = response["intermediate_steps"][0]["query"]
        
        st.subheader("📝 Generated SQL Query:")
        st.code(sql_query, language="sql")

else:
    st.warning("Please enter your Gemini API key and upload a CSV file to proceed.")

