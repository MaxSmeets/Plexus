from server.utils import logger_hook
from agno.tools import tool


@tool(
    name="Add",                
    description="Add two integers",  
    show_result=False,                              
    stop_after_tool_call=False,                      
    tool_hooks=[logger_hook],                       
    requires_confirmation=False,                     
    cache_results=False,                             
    cache_dir="/tmp/agno_cache",                    
    cache_ttl=3600 
)
def add(x: int, y: int) -> int:
    """Adds two integers."""
    return x + y