from typing import Annotated
from pydantic import BaseModel, Field
from typing import Literal
from langgraph.graph.message import add_messages
from langchain.messages import AnyMessage
from langchain_core.messages import ToolMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END

from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt

from tools.email_tool import email_tool
from tools.calender_tool import calendar_tool

from dotenv import load_dotenv
load_dotenv()

llm = init_chat_model("gpt-5.2")

class State(BaseModel):
  messages: Annotated[list[AnyMessage], add_messages]
  approval_status: Literal["approved", "rejected", "modify"] | None = None
  approval_reason: str | None = None
  human_approval_input: str | None = None

def needs_approval_router(state: State):
  last_msg = state.messages[-1]
  return (
    "needs_approval"
    if getattr(last_msg, "tool_calls", None)
    and len(last_msg.tool_calls) > 0
    else "no_approval"
  )

def approval_node(state: State):
  last_msg = state.messages[-1]
  if not getattr(last_msg, "tool_calls", None):
    return {}
  tools_summary = "\n".join(
    f"- {tc['name']}({tc['args']})" for tc in last_msg.tool_calls
  )

  human_response = interrupt(
    f"""
   Proposed action(s):
    {tools_summary}

    Reply with:
    - approved
    - rejected
    - modify
    """
  )
  return {"human_approval_input": str(human_response)}

def interpret_approval(state: State):
    text = state.human_approval_input
    if not text:
      return {}
    text = text.strip().lower()
    if text in {
      "approved", "approve", "yes", "yes send it", "send it",
      "ok", "okay", "go ahead", "confirm"
    }:
      return {
        "approval_status": "approved",
        "approval_reason": text,
        "human_approval_input": None,
      }
    if text in {
      "rejected", "reject", "no", "cancel", "don't send"
    }:
      return {
        "approval_status": "rejected",
        "approval_reason": text,
        "human_approval_input": None,
      }
    return {
      "approval_status": "modify",
      "approval_reason": text,
      "human_approval_input": None,
    }

def approval_router(state : State) :
  return state.approval_status or "rejected"

def clear_approval(state: State):
  return {"approval_status": None, "approval_reason": None, "human_approval_input": None}

def handle_rejection(state: State):
  """Close any pending tool calls by emitting ToolMessages so that
    the conversation history remains OpenAI-protocol valid."""
  status = state.approval_status
  reason = state.approval_reason
  for msg in reversed(state.messages):
    if getattr(msg, "tool_calls", None):
      tool_responses = [
        ToolMessage(
          content=f"Tool call was {status} by user. Reason: {reason or 'N/A'}",
          tool_call_id=tc["id"],
        )
        for tc in msg.tool_calls
      ]
      return {"messages": tool_responses, "approval_status": None, "approval_reason": None, "human_approval_input": None}
  return {"approval_status": None, "approval_reason": None, "human_approval_input": None}

tools = [email_tool, calendar_tool]
llm_with_tools = llm.bind_tools(tools = tools)

def chatbot(state : State) :
  last_msg = state.messages[-1]

  if getattr(last_msg, "tool_calls", None):
    return {}
  new_message = llm_with_tools.invoke(state.messages)  
  return {"messages": [new_message]}

def create_chat_graph(checkpointer):
  builder = StateGraph(State)
  builder.add_node("chatbot",chatbot)
  builder.add_node("approval_node",approval_node)
  builder.add_node("interpret_approval",interpret_approval)
  builder.add_node("clear_approval",clear_approval)
  builder.add_node("handle_rejection",handle_rejection)
  builder.add_node("tools",ToolNode(tools=tools))
  
  builder.add_edge(START, "chatbot")
  builder.add_conditional_edges(
    "chatbot",
    needs_approval_router,
    {
        "needs_approval": "approval_node",
        "no_approval": END,
    }
  )
  builder.add_edge("approval_node", "interpret_approval")
  builder.add_conditional_edges(
    "interpret_approval",
    approval_router,
    {
      "approved": "tools",
      "rejected": "handle_rejection",
      "modify": "handle_rejection"
    }
  )
  builder.add_edge("tools", "clear_approval")
  builder.add_edge("clear_approval", END)
  builder.add_edge("handle_rejection", END)

  return builder.compile(checkpointer=checkpointer)
  