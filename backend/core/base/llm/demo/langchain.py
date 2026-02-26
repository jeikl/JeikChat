import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 关键：使用相对路径向上4级（从demo到backend）
env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../..", ".env")
)
print("Debug: .env file path:", env_path)
load_dotenv(dotenv_path=env_path, override=True)


