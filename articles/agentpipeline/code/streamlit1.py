
from crewai import Agent, Task, Crew

import os
# OpenAI
<<<<<<< HEAD
os.environ["OPENAI_API_KEY"] = "your api key"
=======
os.environ["OPENAI_API_KEY"] = "your api code"
>>>>>>> c8b9cb2 (update)

llm = "gpt-4o"

# Create the wikipedia tool
from crewai_tools import tool
import wikipedia

@tool("wikipedia_lookup")
def wikipedia_lookup(q: str) -> str:
    "Look up a query in Wikipedia and return a summary"
    return wikipedia.page(q).summary

# Define the agent
intelligent_wikipedia = Agent(
        role="Researcher",
        goal="You research topics using Wikipedia and report on the results",
        backstory="You are an experienced writer and editor",
        tools=[wikipedia_lookup],
        allow_delegation=False,
        llm=llm

    )

# The run function sets the task and executes the crew
# and returns the result
def run(s: str):
    task = Task(
        description=s,
        expected_output='A short text based on the tool output',
        agent=intelligent_wikipedia,
        tools=[wikipedia_lookup]
    )

    # Define the crew
    crew = Crew(
        agents=[intelligent_wikipedia],
        tasks=[task],
        verbose=True
    )

    result = crew.kickoff()
    task_output = task.output
    return task_output.raw
    
###############################

import streamlit as st

st.header("Intelligent Wikipedia")

if q := st.text_input("Enter your question"):
    answer = run(q)
    print(answer)
    st.markdown( answer)