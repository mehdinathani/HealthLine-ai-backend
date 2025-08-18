# main.py

import asyncio
from agents import Runner, set_tracing_disabled, enable_verbose_stdout_logging
from geminiConfig import gemini_config
from app.my_agents import master_agent

# Disabling tracing for a cleaner console output
set_tracing_disabled(True)

async def main():
    print("--- HealthLine AI Assistant ---")
    print("Ask about doctor schedules or book an appointment. Type 'exit' to quit.")
    enable_verbose_stdout_logging()

    # Step 1: Initialize the history list for this session
    # This list will store the entire conversation.
    # The format matches what the agent framework expects: a list of dictionaries.
    history = []

    while True:
        try:
            user_input = input("\nYou > ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting. Thank you for using HealthLine!")
                break
            
            if not user_input:
                continue

            print("\nAssistant is thinking...")
            
            # Step 2: Append the user's new message to the history
            history.append({"role": "user", "content": user_input})
            
            # Step 3: Run the agent, passing the *entire* history as input
            result = await Runner.run(
                starting_agent=master_agent,
                input=history,  # <-- We now pass the whole conversation
                run_config=gemini_config,
            )

            # Step 4: Append the assistant's response to the history
            # This ensures the agent remembers its own replies in the next turn.
            if result.final_output:
                history.append({"role": "assistant", "content": result.final_output})

            # Print the final output from the agent
            print(f"\nAssistant > {result.final_output}")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Please try again.")

if __name__ == "__main__":
    asyncio.run(main())