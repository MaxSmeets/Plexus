import os
from textwrap import dedent

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.models.mistral import MistralChat
import dotenv

dotenv.load_dotenv()
mistral_api_key = os.getenv("MISTRAL_API_KEY")

# Define tools to manage our shopping list
def add_item(agent: Agent, item: str) -> str:
    """Add an item to the shopping list and return confirmation."""
    # Add the item if it's not already in the list
    if item.lower() not in [i.lower() for i in agent.session_state["shopping_list"]]:
        agent.session_state["shopping_list"].append(item)
        return f"Added '{item}' to the shopping list"
    else:
        return f"'{item}' is already in the shopping list"


def remove_item(agent: Agent, item: str) -> str:
    """Remove an item from the shopping list by name."""
    # Case-insensitive search
    for i, list_item in enumerate(agent.session_state["shopping_list"]):
        if list_item.lower() == item.lower():
            agent.session_state["shopping_list"].pop(i)
            return f"Removed '{list_item}' from the shopping list"

    return f"'{item}' was not found in the shopping list"


def list_items(agent: Agent) -> str:
    """List all items in the shopping list."""
    shopping_list = agent.session_state["shopping_list"]

    if not shopping_list:
        return "The shopping list is empty."

    items_text = "\n".join([f"- {item}" for item in shopping_list])
    return f"Current shopping list:\n{items_text}"


# Create a Shopping List Manager Agent that maintains state
shopping_list_agent = Agent(
    model=MistralChat(
        id="mistral-medium-latest",
        api_key=mistral_api_key,
        temperature=0.2
    ),
    # Initialize the session state with an empty shopping list
    session_state={"shopping_list": []},
    tools=[add_item, remove_item, list_items],
    # You can use variables from the session state in the instructions
    instructions=dedent("""\
        Your job is to manage a shopping list.

        You can add items, remove items by name, and list all items.
        Use the tools provided to perform these actions.

        Current shopping list: {shopping_list}
    """),
    show_tool_calls=True,
    add_state_in_messages=True,
    markdown=True,
    stream=True,
)