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

            # Debugging: Show full response (moved into an expander)
            with st.expander("🛠 Debug: Full Agent Response"):
                st.json(response)

            # Extract and Display SQL Query
            if "intermediate_steps" in response:
                try:
                    # Assuming the SQL query is the first part of the first tuple in intermediate_steps
                    sql_query_step = response["intermediate_steps"][0]
                    if isinstance(sql_query_step, tuple) and len(sql_query_step) > 1:
                        # The actual SQL query might be nested if action_log is present
                        action_log = sql_query_step[0]
                        if hasattr(action_log, 'tool_input') and isinstance(action_log.tool_input, str) :
                            sql_query = action_log.tool_input
                        elif isinstance(sql_query_step[1], str) : # Fallback if no action_log or tool_input
                            sql_query = sql_query_step[1]
                        else: # Deeper nesting or different structure
                            # Attempt to find a string that looks like a SQL query
                            sql_query = "Could not reliably extract SQL query. Check debug response."
                            for item in sql_query_step:
                                if isinstance(item, str) and ("SELECT" in item.upper() or "INSERT" in item.upper() or "UPDATE" in item.upper() or "DELETE" in item.upper()):
                                    sql_query = item
                                    break
                                elif isinstance(item, dict) and 'query' in item: # Langchain SQLDatabaseTool sometimes returns a dict
                                    sql_query = item['query']
                                    break


                    elif isinstance(sql_query_step, str): # Simpler case if it's just a string
                        sql_query = sql_query_step
                    else:
                        sql_query = "SQL query format not recognized in intermediate_steps."

                    st.subheader("Generated SQL Query")
                    st.code(sql_query, language="sql")
                except Exception as e:
                    st.warning(f"Could not extract SQL query from intermediate steps: {str(e)}")

            st.divider() # Visually separate SQL query from results
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
