from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain.messages import AnyMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END

load_dotenv()

class State(TypedDict):
  messages: Annotated[list[AnyMessage], add_messages]

llm = init_chat_model("gpt-5.2")

def chatbot(state : State) :
  new_message = llm.invoke(state["messages"])  
  return {"messages": [new_message]}


def create_chat_graph(checkpointer):
  builder = StateGraph(State)
  builder.add_node("chatbot",chatbot)
  builder.add_edge(START, "chatbot")
  builder.add_edge("chatbot", END)

  return builder.compile(checkpointer=checkpointer)
