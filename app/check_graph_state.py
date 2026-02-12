from dotenv import load_dotenv
from app.graph import create_chat_graph
from langgraph.checkpoint.mongodb import MongoDBSaver


load_dotenv()
MONGODB_URI = "mongodb://admin:admin@localhost:27017"
config={"configurable": {"thread_id": "9"}}

def check():
    with MongoDBSaver.from_conn_string(MONGODB_URI) as checkpointer:
        graph = create_chat_graph(checkpointer)
        state = graph.get_state(config=config)
        for message in state.values['messages']:
            message.pretty_print()

check()
