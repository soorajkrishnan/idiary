from dotenv import load_dotenv

load_dotenv()

from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langgraph.checkpoint.sqlite import SqliteSaver

# Create the agent
memory = SqliteSaver.from_conn_string(":memory:")


llm_model = OllamaFunctions(model="mistral")
search = DuckDuckGoSearchRun()
tools = [search]
agent_executor = create_react_agent(llm_model, tools, checkpointer=memory)
# Use the agent
config = {"configurable": {"thread_id": "abc123"}}
for chunk in agent_executor.stream(
    {"messages": [HumanMessage(content="hi im bob! and i live in sf")]}, config
):
    print(chunk)
    print("----")

for chunk in agent_executor.stream(
    {"messages": [HumanMessage(content="whats the weather where I live?")]}, config
):
    print(chunk)
    print("----")