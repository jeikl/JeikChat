import asyncio
import sys
import traceback

async def check_saver():
    print("--- Checking AsyncPostgresSaver ---")
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        print("Imported AsyncPostgresSaver from langgraph.checkpoint.postgres.aio")
    except ImportError:
        try:
            from langgraph.checkpoint.postgres import AsyncPostgresSaver
            print("Imported AsyncPostgresSaver from langgraph.checkpoint.postgres")
        except ImportError:
            print("Failed to import AsyncPostgresSaver")
            return

    DB_URI = "postgresql://root:anhuang520@pan.junv.top:5432/postgres?sslmode=disable"
    
    try:
        async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
            print("Checkpointer created")
            try:
                await checkpointer.setup()
                print("Setup done")
            except Exception as e:
                print(f"Setup failed: {e}")
            
            config = {"configurable": {"thread_id": "test_script_1"}}
            try:
                # Use aget_tuple if available (LangGraph 0.2+)
                if hasattr(checkpointer, 'aget_tuple'):
                    print("Calling aget_tuple...")
                    await checkpointer.aget_tuple(config)
                    print("aget_tuple success")
                else:
                    print("aget_tuple not found")
            except NotImplementedError:
                print("aget_tuple raised NotImplementedError")
                traceback.print_exc()
            except Exception as e:
                print(f"aget_tuple raised {type(e).__name__}: {e}")
                traceback.print_exc()

    except Exception as e:
        print(f"General Error: {e}")
        traceback.print_exc()

def check_create_agent():
    print("\n--- Checking create_agent ---")
    try:
        from langchain.agents import create_agent
        print(f"create_agent found in langchain.agents: {create_agent}")
    except ImportError:
        print("create_agent NOT found in langchain.agents")
    except Exception as e:
        print(f"Error checking create_agent: {e}")

    try:
        from langgraph.prebuilt import create_react_agent
        print(f"create_react_agent found in langgraph.prebuilt: {create_react_agent}")
    except ImportError:
        print("create_react_agent NOT found in langgraph.prebuilt")

if __name__ == "__main__":
    check_create_agent()
    asyncio.run(check_saver())
