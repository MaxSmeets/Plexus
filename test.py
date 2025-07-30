from agno.agent.agent import Agent
from agno.app.agui.app import AGUIApp
from agno.models.mistral import MistralChat
import dotenv
import os

dotenv.load_dotenv()
mistral_api_key = os.getenv("MISTRAL_API_KEY")

chat_agent = Agent(
    name="Assistant",
    model=MistralChat(
        id="mistral-medium-latest",
        api_key=mistral_api_key,
        temperature=0.2
    ),
    instructions="You are a helpful AI assistant.",
    add_datetime_to_instructions=True,
    markdown=True,
    stream=True,
)

agui_app = AGUIApp(
    agent=chat_agent,
    name="Basic AG-UI Agent",
    app_id="basic_agui_agent",
    description="A basic agent that demonstrates AG-UI protocol integration.",
)

app = agui_app.get_app()

if __name__ == "__main__":
    agui_app.serve(app="test:app", port=8000, reload=True)