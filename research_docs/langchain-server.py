import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from fastapi import FastAPI
from langserve import add_routes
from dotenv import load_dotenv

load_dotenv()

## load the Groq API key
os.environ['NVIDIA_API_KEY']=os.getenv("NVIDIA_API_KEY")

llm = ChatNVIDIA(model="mixtral_8x7b")

app = FastAPI(
  title="LangChain Server",
  version="1.0",
  description="A simple api server using Langchain's Runnable interfaces",
)

add_routes(
    app,
    llm,
    path="/basic_chat",
    playground_type="chat"
)

## Might be encountered if this were for a standalone python file...
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9012)