import io
from fastapi import FastAPI, File, UploadFile, HTTPException
import requests
import json
from datetime import datetime
import base64
from pydantic import BaseModel
from typing import List

from transformers import pipeline
from supabase import create_client, Client
import numpy as np

# Initialize Supabase client
url = "https://nrgavxxnufxbyolqznop.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5yZ2F2eHhudWZ4YnlvbHF6bm9wIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU4NDMyNjgsImV4cCI6MjA1MTQxOTI2OH0.ze2PsT5sVGgZsGAouEtgIf--JBWwwbvPhhcwSurF_pg"
### Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

class SummarizePayload(BaseModel):
    descriptions: List[str]  # List of descriptions to summarize


class TranscriptPayload(BaseModel):
    transcript: str  # List of descriptions to summarize


    

GROQ_API_KEY = "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"  # Replace with your actual Groq API key

@app.get("/api/py/hi")
async def hi():
    return {"message": "hi"}

@app.post("/api/py/describe-image")
async def describe_image(image: UploadFile = File(...)):
    try:
        # Read the uploaded image
        image_bytes = await image.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        print(encoded_image[:20])
        encoded_image = f"data:image/jpeg;base64,{encoded_image}"
        print(f"Preparing request to Groq API")
        print(f"Encoded image length: {len(encoded_image)}")
        print(f"GROQ_API_KEY set: {bool(GROQ_API_KEY)}")

        headers = {'Authorization': f'Bearer {GROQ_API_KEY}'}
        data = {
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': '''You are an AI assistant expert in describing the actions performed in any sort of image. Return a response of the description of what is happening in the image. 
                            The JSON schema should include:\n\n{\n  "description": str,\n}'''
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': encoded_image
                            }
                        }
                    ]
                }
            ],
            'response_format': {'type': 'json_object'},
            'model': 'llama-3.2-11b-vision-preview',
            'max_tokens': 150,
            'temperature': 0
        }

        # Make the API request
        response = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=data)
        response.raise_for_status()

        # Parse the API response
        chat_completion = response.json()
        parsed_content = json.loads(chat_completion['choices'][0]['message']['content'])
        description = parsed_content.get('description', 'No commentary generated.')

        # Add timestamp
        timestamp = datetime.now()
        formatted_datetime = timestamp.strftime("%A, %B %d, %Y %I:%M:%S %p")
        description = formatted_datetime + ": " + description

        return {"description": description}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/api/py/summarize-descriptions")
async def summarize_descriptions(payload: SummarizePayload):
    
        descriptions = payload.descriptions
        print(descriptions)
        print("hi")
        if not descriptions:
            return {"summary": "No descriptions to summarize."}

        # Prepare request to Groq Llama API
        headers = {'Authorization': f'Bearer {GROQ_API_KEY}'}

        data = {
            'messages': [
            {
            'role': "user",
            'content': f'''You are an AI assistant. Please summarize the following descriptions. Ignore the timestamp:\n\n{descriptions}''',
            },
        ],
        'model': "mixtral-8x7b-32768",
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Groq API error: {response.text}")

        chat_completion = response.json()
        summary = chat_completion["choices"][0]["message"]["content"]

        time = datetime.now().strftime("%A %-d %B %I:%M %p").lower()
        summary = time + ": " + summary

        print(summary)

        supabase: Client = create_client(url, key)

        # Initialize the feature extraction pipeline
        feature_extraction_pipeline = pipeline("feature-extraction", model="Supabase/gte-small")

        
        # Generate embeddings
        output = feature_extraction_pipeline(summary, return_tensors=True)

        # Pooling (mean) and normalization
        embeddings = np.mean(output[0].numpy(), axis=0)
        normalized_embeddings = embeddings / np.linalg.norm(embeddings)

        # Convert embedding to a Python list
        embedding = normalized_embeddings.tolist()
        
        # Store the vector in Supabase
        response = supabase.table("documents").insert({
            "body": summary,
            "embedding_vector": embedding
        }).execute()

        # Handle response
        print(response.json())

        return {"summary": summary}









@app.post("/api/py/summarize-transcript")
async def summarize_descriptions(payload: TranscriptPayload):
    
        descriptions = payload.transcript

        time = datetime.now().strftime("%A %-d %B %I:%M %p").lower()
        summary = time + ": " + descriptions

        print(summary)

        supabase: Client = create_client(url, key)

        # Initialize the feature extraction pipeline
        feature_extraction_pipeline = pipeline("feature-extraction", model="Supabase/gte-small")

        
        # Generate embeddings
        output = feature_extraction_pipeline(summary, return_tensors=True)

        # Pooling (mean) and normalization
        embeddings = np.mean(output[0].numpy(), axis=0)
        normalized_embeddings = embeddings / np.linalg.norm(embeddings)

        # Convert embedding to a Python list
        embedding = normalized_embeddings.tolist()
        
        # Store the vector in Supabase
        response = supabase.table("documents").insert({
            "body": summary,
            "embedding_vector": embedding
        }).execute()

        # Handle response
        print(response.json())

        return {"summary": summary}
