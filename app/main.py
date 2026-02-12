from dotenv import load_dotenv
from app.graph import create_chat_graph
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.types import Command

load_dotenv()
MONGODB_URI = "mongodb://admin:admin@localhost:27017"
config={"configurable": {"thread_id": "22"}}

def run_stream(graph, user_input):
    for event in graph.stream(user_input, config, stream_mode="values"):
        if "__interrupt__" in event:
            print("Interrupt received. Details:")
            print(event["__interrupt__"])
            
            human_response = input("Enter response for the interrupt: ")
            resume_command = Command(resume=human_response)
            for event in graph.stream(resume_command, config, stream_mode="values"):
                if "messages" in event:
                    event["messages"][-1].pretty_print()
            return
        elif "messages" in event:
            event["messages"][-1].pretty_print()
    
def main():
    with MongoDBSaver.from_conn_string(MONGODB_URI) as checkpointer:
        graph = create_chat_graph(checkpointer)
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() in {"exit", "quit"}:
                    break
                run_stream(graph, {"messages": [{"role": "user", "content": user_input}]})
            except KeyboardInterrupt:
                print("\nExiting...")
                break

if __name__ == "__main__":
    main()
