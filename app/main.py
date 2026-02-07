from dotenv import load_dotenv
from graph import create_chat_graph
from langgraph.checkpoint.mongodb import MongoDBSaver


load_dotenv()
MONGODB_URI = "mongodb://admin:admin@localhost:27017"
config={"configurable": {"thread_id": "1"}}

def main():
    with MongoDBSaver.from_conn_string(MONGODB_URI) as checkpointer:
        graph = create_chat_graph(checkpointer)
        while True:
            user_input = input("> ")
            for event in graph.stream({"messages" : [{"role" : "user" , "content" : user_input}]}, config, stream_mode="values"):
                if "messages" in event:
                    event["messages"][-1].pretty_print()


if __name__ == "__main__":
    main()
