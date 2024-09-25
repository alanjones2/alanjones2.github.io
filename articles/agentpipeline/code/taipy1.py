from crewai import Agent, Task, Crew
import mesop as me
import mesop.labs as mel

import os
# OpenAI
os.environ["OPENAI_API_KEY"] = "your api key"

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
        expected_output='A short text based on the tool output.',
        agent=intelligent_wikipedia,
        tools=[wikipedia_lookup]
    )

    # Execute the crew
    crew = Crew(
        agents=[intelligent_wikipedia],
        tasks=[task],
        verbose=True
    )

    result = crew.kickoff()
    task_output = task.output
    return task_output.raw
    

#######

from taipy.gui import Gui
import taipy.gui.builder as tgb

user_input = ""
result = ""

def input_change(state):
    answer = run(state.user_input)
    print(answer)
    state.result = answer

with tgb.Page() as page:
    tgb.text("# Intelligent Wikipedia", mode='md')
    
    with tgb.layout(columns="1 1"):
        with tgb.part():
            tgb.text("Enter your question in the box")
            tgb.input("{user_input}", multiline=False, class_name="fullwidth")
            tgb.button("Submit", on_action=input_change)
        with tgb.part():
            tgb.text("Intellligent Wikipedia's response will appear below:")
            tgb.text("{result}")
        

Gui(page=page).run(dark_mode=True)