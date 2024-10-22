# from contextlib import asynccontextmanager

# from fastapi import FastAPI

# from clients import redis
# from models.recommendation import get_retrieval_model
# from routers.home import router as home_router
# from routers.travel_time import router as travel_time_router
# from routers.recommendation import router as recommendation_router
# from routers.healthz import router as healthz_router

import uuid
from typing import List
 
# FastAPI
from fastapi import FastAPI
from pydantic import BaseModel
 
## Streaming Response utility
from fastapi.responses import StreamingResponse
 
## Enable CORS utility
from fastapi.middleware.cors import CORSMiddleware
 
# Fireworks SDK
import fireworks.client
import os
fireworks.client.api_key = os.environ["FIREWORKS_API_KEY"]
 
# SurrealDB Vector Store SDK for LangChain
from langchain_community.vectorstores import SurrealDBStore
 
# Fireworks Embeddings Integration via LangChain
from langchain_fireworks import FireworksEmbeddings
# Load the nomic-embed-text-v1.5 embedding models via Langchain Fireworks Integration
embeddings = FireworksEmbeddings(model="nomic-ai/nomic-embed-text-v1.5",
                                 fireworks_api_key=os.getenv("FIREWORKS_API_KEY"))


dburl = "ws://localhost:4304/rpc"
db_user = "root"
db_pass = "root"
vector_collection = "vectors" # the collection name of the vector store to and from which the relevant vectors will be inserted and queried from

vector_db = SurrealDBStore(dburl=dburl,
                           db_user=db_user,
                           db_pass=db_pass,
                           collection=vector_collection,
                           embedding_function=embeddings)




# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Application Startup!")
#     # Load the ML models
#     await get_retrieval_model()
#     # model_loading_output = await load_retrieval_model()
#     # print(f"Retrieval Model Loaded in {model_loading_output['execution_time_ms']:.2f} ms")
#     # and establish database connections
#     redis.get_redis_client()
#     #ml_models["model1"] = models.model1.load()
#     #redis_repo.get_instance()
#     yield
#     # Clean up the ML models,
#     # release the resources
#     # and close the connections
#     #ml_models.clear()
#     #redis_repo.close()
#     print("Application shutdown!")


# app = FastAPI(title="Telco LLM", lifespan=lifespan)
app = FastAPI(title="Telco LLM")

# Add CORS middleware, allows your frontend to successfully POST to the RAG application endpoints to fetch responses to the user query, regardless of the port it is running on.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# app.include_router(home_router)
# app.include_router(travel_time_router)
# app.include_router(recommendation_router)
# app.include_router(healthz_router)


# @app.middleware("http")
# async def log_requests(request, call_next):
#     # Log the incoming request
#     print(f"Incoming Request: {request.method} {request.url}")
#
#     # Proceed with handling the request
#     response = await call_next(request)
#
#     # Log the outgoing response
#     print(f"Outgoing Response: {response.status_code}")
#
#     return response


# Class representing the string of messages to be searched and embedded as system context.
class LearningMessages(BaseModel):
    alarms: str
 
# Class representing a single message of the conversation between RAG application and user.
class Message(BaseModel):
    role: str
    content: str
 
# Class representing collection of messages above.
class Messages(BaseModel):
    messages: List[Message]


@app.post('/add-new-alarms')
async def add_new_alarms(messages: LearningMessages): # Accepts a single string as messages containing comma (,) separated messages to be inserted in your SurrealDB vector store.
    messages_json = messages.model_dump()["alarms"].split(',')
    # Initialize SurrealDB
    await vector_db.initialize()
    # Create texts to be inserted into the Vector Store (Embeddings are generated automatically)
    metadatas = [{"len": len(t), "remedy": "REMEDY!"} for t in messages_json]
    ids = [str(uuid.uuid4()) for _ in messages_json]
    await vector_db.aadd_texts(messages_json, metadatas=metadatas, ids=ids)
