
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

# Define the agents
researcher_agent = Agent(
        role="Researcher",
        goal="You research topics using Wikipedia and report on the results",
        backstory="You are an experienced writer and editor",
        tools=[wikipedia_lookup],
        llm=llm
    )

writer_agent = Agent(
        role="Writer",
        goal="You re-write articles so that they are suitable for young readers",
        backstory="You are an experienced writer and editor",
        llm=llm

    )
editor_agent = Agent(
        role="Editor",
        goal="You ensure that the text you are given is grammatically correct and the correct length",
        backstory="You are an experienced writer and editor",
        llm=llm
    )

# The run function sets the task and executes the crew
# and returns the result
def run(s: str):
    task1 = Task(
        description=q,
        expected_output='A short text based on the tool output',
        agent=researcher_agent,
        tools=[wikipedia_lookup]
    )

    task2 = Task(
        description="Rework the text to be suitable for a 10-year-old reader",
        expected_output='A short text based on the tool output',
        agent=writer_agent,
    )

    task3 = Task(
        description="Edit the text to ensure that it is grammatically correct and no more than 500 words",
        expected_output='A short text based on the tool output',
        agent=editor_agent,
    )

    # Define the crew
    crew = Crew(
        agents=[researcher_agent, writer_agent, editor_agent],
        tasks=[task1, task2, task3],
        verbose=True
    )

    result = crew.kickoff()

    return result.raw    
###############################

import streamlit as st

st.header("Wikipedia for kids")

if q := st.text_input("Enter your question"):
    answer = run(q)
    print(answer)
    st.markdown( answer)