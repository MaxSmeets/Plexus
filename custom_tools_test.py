from agno.agent import Agent
from agno.models.ollama  import Ollama
from agno.eval.accuracy import AccuracyEval
from agno.tools import tool
from typing import Any, Callable, Dict

def logger_hook(function_name: str, function_call: Callable, arguments: Dict[str, Any]):
    """Hook function that wraps the tool execution"""
    print(f"About to call {function_name} with arguments: {arguments}")
    result = function_call(**arguments)
    print(f"Function call completed with result: {result}")
    return result

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

agent = Agent(
    model=Ollama("llama3.2:latest"),
    tools=[add],
    instructions="You are a helpful assistant. Use the tools provided to answer questions if relevant.",
    markdown=True,  
    monitoring=True,
    stream=True,
)

eval = AccuracyEval(
    model=Ollama("llama3.2:latest"),
    agent=Agent(model=Ollama("llama3.2:latest")),
    input="What is 10*5 then to the power of 2? do it step by step",
    expected_output="2500",
    monitoring=True,
)

agent.print_response("What's 352 + 643?")