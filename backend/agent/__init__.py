from langchain.agents import create_agent
from langgraph.checkpoint.postgres import PostgresSaver

from services.llm import create_client
from chatRouterStream import tools
DB_URI = "postgresql://root:anhuang520@pan.junv.top:5432/postgres?sslmode=disable"



checkpointer = PostgresSaver.from_conn_string(DB_URI)
#checkpointer.setup()
