import os
from textwrap import dedent

from agno.app.agui.app import AGUIApp
from agno.agent import Agent
from agno.models.mistral import MistralChat
import dotenv

dotenv.load_dotenv()
mistral_api_key = os.getenv("MISTRAL_API_KEY")

# Create a simple helpful assistant agent without tools
helpful_agent = Agent(
    model=MistralChat(
        id="mistral-medium-latest",
        api_key=mistral_api_key,
        temperature=0.7
    ),
    instructions=dedent("""\
        You are a helpful AI assistant. You can answer questions, provide information,
        and have conversations on a wide variety of topics. Be friendly, informative,
        and concise in your responses.
    """),
    add_datetime_to_instructions=True,
    markdown=True,
)

# Setup the AG-UI app
agui_app = AGUIApp(
    agent=helpful_agent,
    name="Plexus Helpful Assistant",
    app_id="plexus_helpful_agent",
    description="A helpful AI assistant that can answer questions, provide information, and have conversations on a wide variety of topics. Built with Agno and AG-UI protocol for seamless frontend integration.",
)

# Get the FastAPI app instance
app = agui_app.get_app()

# Serve the app when run directly
if __name__ == "__main__":
    agui_app.serve(app="basic:app", port=8000, reload=True)
