import os
from dotenv import load_dotenv
# Change: Import ChatGroq instead of ChatOpenAI
from langchain_groq import ChatGroq 

load_dotenv()

# Change: Initialize ChatGroq and pick a Groq-supported model 
# Popular models: "llama-3.3-70b-versatile", "llama3-8b-8192", or "mixtral-8x7b-32768"
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

# The rest of the logic remains the same
print(llm.invoke("Xin chào?").content)