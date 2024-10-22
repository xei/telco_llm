import uuid
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import weaviate
from langchain_community.vectorstores import Weaviate
import os

# Fireworks SDK
import fireworks.client
fireworks.client.api_key = os.environ["FIREWORKS_API_KEY"]

# Fireworks Embeddings Integration via LangChain
from langchain_fireworks import FireworksEmbeddings

# https://python.langchain.com/docs/integrations/text_embedding/fireworks/
embeddings = FireworksEmbeddings(model="nomic-ai/nomic-embed-text-v1.5",
                                 fireworks_api_key=os.getenv("FIREWORKS_API_KEY"))

# https://api.python.langchain.com/en/latest/vectorstores/langchain_community.vectorstores.weaviate.Weaviate.html
# https://python.langchain.com/docs/integrations/vectorstores/weaviate/
client = weaviate.Client(url="http://weaviate:8080")
index_name = "Alarm"
text_key = "content"
weaviate = Weaviate(client, index_name, text_key, embeddings)

class LearningMessages(BaseModel):
    alarms: str

class Message(BaseModel):
    role: str
    content: str

class Messages(BaseModel):
    messages: List[Message]

app = FastAPI(title="Telco LLM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AddNewAlarmRequestPayload(BaseModel):
    alarm: str = Field(
        description="Alarm Details",
        example="024-08-28 14:59:19	Major	1060027454	User Plane Fault	Communication Alarm	Service Type=X2 LINK_FAILURE Communication Alarm	CLUSTER 1	G4023	Service Type=X2	MKTG4023HUB3001	HUAWEI	5G"
    )
    remedy: str = Field(
        description="Remedy",
        example="Step1: ..., Step2: ..."
    )


@app.post("/add_new_alarm")
async def add_new_alarm(request_payload: AddNewAlarmRequestPayload):
    try:
        # Split the alarms and create metadata
        messages_json = request_payload.alarm.split(',')
        metadatas = [{"len": len(t), "remedy": request_payload.remedy, "original_alarm": request_payload.alarm} for t in messages_json]
        ids = [str(uuid.uuid4()) for _ in messages_json]

        # Add texts to Weaviate
        await weaviate.aadd_texts(messages_json, metadatas=metadatas, ids=ids)
        
        # Optionally return a success response
        return {"message": "Update successful", "ids": ids}

    except Exception as e:
        # Log the exception (optional)
        print(f"Error updating messages: {e}")

        # Raise an HTTP exception with a 500 status code
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/retrieve")
async def retrieve_relevant_alarms(query: str):
    try:
        query_vector = embeddings.embed_query(query)
        relevant_content = await weaviate.asimilarity_search_by_vector(query_vector, 2)
       # relevant_content = await weaviate.asimilarity_search(query)
        return relevant_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
