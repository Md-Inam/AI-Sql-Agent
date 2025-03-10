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
uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])

# Main UI
st.title("🧠 AI-Powered SQL Agent")
st.write("Ask questions in plain English and get both the **SQL query** and the **result**!")

# Use default data if no file is uploaded
if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    # Default sample data (Replace with a relevant dataset)
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

            # Extract SQL query from AI response
            sql_command = None
            if "sql_cmd" in response:
                sql_command = response["sql_cmd"]
            elif "intermediate_steps" in response and response["intermediate_steps"]:
                for step in response["intermediate_steps"]:
                    if isinstance(step, tuple) and len(step) > 1 and "query" in step[1]:
                        sql_command = step[1]["query"]
                        break

            if not sql_command:
                sql_command = "⚠️ No SQL command was generated."

            # Extract Query Result
            query_result = response.get("output", "⚠️ No result available.")

            # Display SQL Query & Result
            st.subheader("🔍 Generated SQL Query")
            st.code(sql_command, language="sql")

            st.subheader("📊 Query Result")
            st.write(query_result)
        else:
            # Process query using Pandas when no API key is provided
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
