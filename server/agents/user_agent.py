import asyncio 
from agno.agent import Agent
from agno.models.ollama import Ollama

async def user_agent():
    agent = Agent(
        model=Ollama("llama3.2:latest"),
        tools=[],
        instructions="You are a helpful assistant called Ada. Answer the user's questions to the best of your ability.",
        markdown=True,
        monitoring=True,
        stream=True,
        reasoning=False
    )

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting the chat.")
            break
        await agent.aprint_response(user_input)

if __name__ == "__main__":
    asyncio.run(user_agent())

        