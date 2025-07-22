from agno.agent import Agent
from agno.models.ollama  import Ollama
from agno.eval.accuracy import AccuracyEval

agent = Agent(
    model=Ollama("llama3.2:latest"),
    instructions="You are a helpful assistant.",
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

result = eval.run(print_results=True)