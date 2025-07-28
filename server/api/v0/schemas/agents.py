"""
Agent-related schemas for the Plexus API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """Request model for agent interactions."""
    
    message: str = Field(..., description="User message for the agent", min_length=1)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the agent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Create a shopping list for pasta dinner",
                "context": {"dietary_restrictions": ["vegetarian"]}
            }
        }


class AgentResponse(BaseModel):
    """Response model for agent interactions."""
    
    response: str = Field(..., description="Agent response")
    agent_type: str = Field(..., description="Type of agent that processed the request")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Here's your shopping list for pasta dinner...",
                "agent_type": "shopping_list_agent",
                "metadata": {"items_count": 5, "estimated_cost": 25.50}
            }
        }


class ShoppingListItem(BaseModel):
    """Shopping list item model."""
    
    name: str = Field(..., description="Item name")
    quantity: str = Field(..., description="Item quantity")
    category: Optional[str] = Field(None, description="Item category")
    estimated_price: Optional[float] = Field(None, description="Estimated price")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Spaghetti pasta",
                "quantity": "1 lb",
                "category": "Pantry",
                "estimated_price": 2.99
            }
        }


class ShoppingListResponse(BaseModel):
    """Shopping list response model."""
    
    items: List[ShoppingListItem] = Field(..., description="List of shopping items")
    total_items: int = Field(..., description="Total number of items")
    estimated_total: Optional[float] = Field(None, description="Estimated total cost")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "name": "Spaghetti pasta",
                        "quantity": "1 lb",
                        "category": "Pantry",
                        "estimated_price": 2.99
                    }
                ],
                "total_items": 1,
                "estimated_total": 2.99
            }
        }
