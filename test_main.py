# test_main.py

import asyncio
from agents import Runner, set_tracing_disabled, enable_verbose_stdout_logging
# Note: We import from our new test files
from test_agents import simple_agent
from geminiConfig import gemini_config # Your existing config is fine

# Disable extra logging for a clean test
set_tracing_disabled(True)

async def main():
    # enable_verbose_stdout_logging()
    print("--- Starting Minimal Agent Test ---")
    # This input is designed to trigger the simple tool
    user_input = "hello my name is mehdi"
    print(f"Test Input: '{user_input}'")

    result = await Runner.run(
        starting_agent=simple_agent,
        input=user_input,
        run_config=gemini_config,
    )

    print(result.final_output)

    # try:
    #     result = await Runner.run(
    #         starting_agent=simple_agent,
    #         input=user_input,
    #         run_config=gemini_config,
    #     )

    #     print("\n--- Test Result ---")
    #     print(result.final_output)
    #     print("\n--- TEST SUCCEEDED ---")

    # except Exception as e:
    #     print("\n--- !!! TEST FAILED !!! ---")
    #     print(f"The error occurred even with the simplest possible tool.")
    #     print(f"Error Type: {type(e).__name__}")
    #     print(f"Error Details: {e}")

if __name__ == "__main__":
    asyncio.run(main())