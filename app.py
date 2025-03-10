import os
import sys
import subprocess

# Install openpyxl if not already installed
try:
    import openpyxl
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

import pandas as pd
import streamlit as st


import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from langchain.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI as GenAI
from langchain_community.agent_toolkits import create_sql_agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit UI Layout
st.set_page_config(layout="wide")

# Sidebar for API Key & File Upload
st.sidebar.title("🔑 API Key & File Upload")
api_key = st.sidebar.text_input("Enter your Google API Key", type="password")
uploaded_file = st.sidebar.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

# Main UI
st.title("🧠 AI-Powered SQL Agent")
st.write("Ask questions in plain English and get instant results!")

# Handle file upload
if uploaded_file:
    file_extension = uploaded_file.name.split(".")[-1]

    try:
        if file_extension == "csv":
            df = pd.read_csv(uploaded_file)
        elif file_extension == "xlsx":
            df = pd.read_excel(uploaded_file, engine="openpyxl")  # Ensures compatibility with different Excel formats
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            st.stop()
    except Exception as e:
        st.error(f"⚠️ Error reading file: {str(e)}")
        st.stop()

else:
    # Default dataset
    data = {
        "ID": [1, 2, 3, 4, 5],
        "Name": ["Alice", "Bob", "Charlie", "David", "Emma"],
        "Age": [25, 30, 35, 40, 45],
        "Salary": [50000, 60000, 70000, 80000, 90000]
    }
    df = pd.DataFrame(data)
    st.warning("⚠️ No file uploaded. Using default sample dataset.")

# Create SQLite database
engine = create_engine("sqlite:///uploaded_data.db")
df.to_sql("uploaded_table", engine, index=False, if_exists='replace')

# Initialize SQL database
db = SQLDatabase(engine=engine)

# Create AI Agent
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    llm = GenAI(model="gemini-1.5-flash", temperature=0, google_api_key=api_key)
    agent_executor = create_sql_agent(llm, db=db, verbose=True, return_intermediate_steps=True)
else:
    st.warning("⚠️ No API key provided. AI features disabled.")

# Query Input
query = st.text_input("Enter your question:")

if query:
    try:
        if api_key:
            # AI Processing
            response = agent_executor(query)

            # Debugging: Show full response
            st.subheader("🛠 Debug: Full Response")
            st.json(response)  # Display full response for debugging

            # Extract Query Result
            query_result = response.get("output", "⚠️ No result available.")

            # Display Result
            st.subheader("📊 Query Result")
            st.write(query_result)

        else:
            # Pandas Fallback Query Execution
            st.warning("⚠️ AI is disabled. Running query using Pandas.")

            # Try to execute the query manually on DataFrame
            try:
                result = df.query(query)
                st.subheader("📊 Query Result")
                st.write(result)
            except Exception as e:
                st.error(f"⚠️ Invalid query: {str(e)}")

    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
