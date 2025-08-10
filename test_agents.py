# test_agents.py

from agents import Agent
# Note: We import from our new test_tools file
from test_tools1 import say_hello 

simple_agent: Agent = Agent(
    name="Simple Test Agent",
    instructions="You are a simple agent. Your only job is to say hello to the user by using your 'say_hello' tool. Do not do anything else.",
    tools=[say_hello],
)