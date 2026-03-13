from langchain_unstructured import UnstructuredLoader

file_paths = [
    "F:/code/aichat/backend/agent/knowledges/懂王-Ai应用开发架构师-就业班3.0-冲击月薪40k.pdf"
]

loader = UnstructuredLoader(file_paths)

docs=loader.load()
print(len(docs))
