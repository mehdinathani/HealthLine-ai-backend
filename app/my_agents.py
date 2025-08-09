from agents import Agent
from app.my_tools import (
    find_doctor_by_name,
    list_doctors_by_specialty,
    check_availability,
    book_appointment,
)

master_agent : Agent = Agent(
    name="Master Agent",
    instructions="You are the master agent. You can delegate tasks to other agents.",
    tools=[
        find_doctor_by_name,
        list_doctors_by_specialty,
        check_availability,
        book_appointment,
    ]
)




