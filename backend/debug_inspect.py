import inspect
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

print(f"AsyncPostgresSaver has aget_tuple: {hasattr(AsyncPostgresSaver, 'aget_tuple')}")
print(f"AsyncPostgresSaver bases: {AsyncPostgresSaver.__bases__}")

from langchain.agents import create_agent
print(f"create_agent module: {create_agent.__module__}")
