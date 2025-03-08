import os
import pandas as pd
from sqlalchemy import create_engine
from langchain.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI as GenAI
from langchain_community.agent_toolkits import create_sql_agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Google Gemini API key (Replace with your actual API key)
os.environ["GOOGLE_API_KEY"] = "your-google-api-key-here"

# Create SQLite database and load dataset
csv_path = "data.csv"  # Change this to your actual CSV file
df = pd.read_csv(csv_path)

# Create SQLite database engine
engine = create_engine("sqlite:///database.db")
df.to_sql("sales_data", engine, index=False, if_exists='replace')

# Initialize SQL database
db = SQLDatabase(engine=engine)

# Initialize AI Model
llm = GenAI(model="gemini-1.5-flash", temperature=0, google_api_key=os.environ["GOOGLE_API_KEY"])

# Create SQL Agent
agent_executor = create_sql_agent(llm, db=db, verbose=True, return_intermediate_steps=True)

# Function to get SQL query instead of executing it
def get_sql_query(question):
    response = agent_executor.invoke({"input": question})
    return response["intermediate_steps"][0]["query"]

# Example Usage
if __name__ == "__main__":
    user_question = "Show all sales from 2023"
    sql_query = get_sql_query(user_question)
    print("Generated SQL Query:")
    print(sql_query)


