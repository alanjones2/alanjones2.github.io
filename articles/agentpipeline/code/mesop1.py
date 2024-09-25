from crewai import Agent, Task, Crew
import mesop as me
import mesop.labs as mel

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
    """Look up a query in Wikipedia and return a summary"""
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
        verbose=False
    )

    result = crew.kickoff()
    task_output = task.output
    return task_output.raw

###############################3
# Set up the UI with Mesop
@me.page(
  path="/",
  title="Intelligent Wikipedia",
)

def app():
  with me.box(style=me.Style(background="#f0f4f8", padding=me.Padding.all(16))):
    me.text("Intelligent Wikipedia", type='headline-4')
    mel.text_to_text(
        run,
        title="Enter a query, below",
    )


    



