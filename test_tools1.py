# test_tools.py

from agents import function_tool
import json

@function_tool
def say_hello(name: str) -> str:
    """A very simple tool that says hello to someone."""
    print(f"\n--- LOG: Tool 'say_hello' was called with name: {name} ---\n")
    msg : str = f"Hello, {name}!"
    return msg