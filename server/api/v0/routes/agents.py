"""
Agent routes for the Plexus API.
"""

from fastapi import APIRouter, Request, HTTPException
from ..schemas import AgentRequest, AgentResponse, SuccessResponse
from ...core import create_response_envelope, PlexusAPIException

# Import the shopping list agent
try:
    from ....agents.shopping_list_agent import shopping_list_agent
except ImportError:
    shopping_list_agent = None

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "/shopping-list",
    response_model=SuccessResponse,
    summary="Shopping List Agent",
    description="Interact with the shopping list agent to generate shopping lists"
)
async def shopping_list_chat(
    request_data: AgentRequest,
    request: Request
) -> SuccessResponse:
    """
    Send a message to the shopping list agent.
    
    The agent will process your request and generate a shopping list
    or provide shopping-related assistance.
    """
    try:
        if shopping_list_agent is None:
            raise PlexusAPIException(
                "Shopping list agent is not available",
                status_code=503
            )
        
        # Get response from the agent
        # Capture the agent's response by temporarily redirecting stdout
        import io
        import contextlib
        
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            shopping_list_agent.print_response(request_data.message)
        
        agent_response_text = output_buffer.getvalue().strip()
        
        # If no output captured, try getting the last message
        if not agent_response_text:
            agent_response_text = "Shopping list agent processed your request."
        
        response_data = AgentResponse(
            response=agent_response_text,
            agent_type="shopping_list_agent",
            metadata={
                "context_provided": request_data.context is not None,
                "message_length": len(request_data.message)
            }
        )
        
        return create_response_envelope(
            data=response_data.dict(),
            message="Agent response generated successfully",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except PlexusAPIException:
        raise
    except Exception as e:
        raise PlexusAPIException(
            f"Error processing agent request: {str(e)}",
            status_code=500
        )


@router.get(
    "/available",
    response_model=SuccessResponse,
    summary="Available Agents",
    description="Get a list of available agents"
)
async def get_available_agents(request: Request) -> SuccessResponse:
    """
    Get a list of all available agents and their capabilities.
    """
    available_agents = []
    
    # Check which agents are available
    if shopping_list_agent is not None:
        available_agents.append({
            "name": "shopping_list_agent",
            "type": "shopping_list",
            "description": "Generates shopping lists and provides shopping assistance",
            "endpoint": "/api/v0/agents/shopping-list",
            "status": "available"
        })
    
    # You can add more agents here as they become available
    # if recipe_agent is not None:
    #     available_agents.append({...})
    
    return create_response_envelope(
        data={
            "agents": available_agents,
            "total_count": len(available_agents)
        },
        message="Available agents retrieved successfully",
        request_id=getattr(request.state, 'request_id', None)
    )
