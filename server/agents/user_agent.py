import asyncio 
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.mcp import MCPTools

async def user_agent():
    async with MCPTools(command="uvx mcp-server-git") as mcp_tools:
        agent = Agent(
            model=Ollama("llama3.2:latest"),
            tools=[mcp_tools],
            instructions="You can use your tools to make git commits and push changes.",
            markdown=True,
            monitoring=True,
            stream=True,
            reasoning=True
        )

        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting the chat.")
                break
            await agent.aprint_response(user_input)

if __name__ == "__main__":
    asyncio.run(user_agent())

        