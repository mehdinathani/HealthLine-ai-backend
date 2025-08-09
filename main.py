# main.py

import asyncio
from agents import Runner, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered, set_tracing_disabled
from geminiConfig import gemini_config
from app.my_agents import master_agent

async def main():
    set_tracing_disabled = True
    result =await Runner.run(
        starting_agent=master_agent,
        # input_guardrail=InputGuardrailTripwireTriggered,
        # output_guardrail=OutputGuardrailTripwireTriggered,
        input="I need a doctor named mehdi.",
        run_config=gemini_config,
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
