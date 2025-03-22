import io
from fastapi import FastAPI, File, UploadFile, HTTPException
import requests
import json
from datetime import datetime
import base64
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer

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
    #store_summary("hi how are you")
    answer = fetch_relevant_context("how are you")
    print(answer)
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

        
        store_summary(description)
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

        timestamp = datetime.now()
        formatted_datetime = timestamp.strftime("%A, %B %d, %Y %I:%M:%S %p")
        summary = formatted_datetime + ": " + summary

        print(summary)

        store_summary(summary)

        
        

        # Handle response
        print(response.json())

        return {"summary": summary}




def store_summary(sentence):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    supabase: Client = create_client(url, key)

    embedding = model.encode(sentence, convert_to_numpy=True)
    
    response = supabase.table("documents").insert({
        "body": sentence,
        "embedding_vector": embedding.tolist()
    }).execute()

    print(response)






@app.post("/api/py/summarize-transcript")
async def summarize_descriptions(payload: TranscriptPayload):
    
        descriptions = payload.transcript
        if not descriptions:
            return {"summary":""}
        timestamp = datetime.now()
        formatted_datetime = timestamp.strftime("%A, %B %d, %Y %I:%M:%S %p")
        summary = formatted_datetime + ": " + descriptions

        print(summary)

        store_summary(summary)

        return {"summary": summary}






def fetch_relevant_context(question: str, top_k: int = 1):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    supabase: Client = create_client(url, key)
    
    question_embedding = model.encode(question, convert_to_numpy=True)

        # Query Supabase to get relevant document matches using RPC
    response = supabase.rpc(
        "match_documents",
        {
            "query_embedding": question_embedding.tolist(),
            "match_threshold": 0.1,  # Example threshold
            "match_count": top_k          # Return top 2 results
        }
    ).execute()
    print(response)
    print(response.data)
    return response.data[0]["body"]



class QuestionPayload(BaseModel):
    question: str

@app.post("/api/py/get-answer")
async def get_answer(payload: QuestionPayload):
    """Generate answer based on the most relevant RAG context."""
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # Fetch top 2 relevant context matches
        context_str = fetch_relevant_context(question)

        # Prepare the prompt for Groq API
        prompt = f"""
        You are an AI assistant. Answer the question accurately addressing the user directly using the following context.
        
        Context:
        {context_str}
        
        Question:
        {question}
        
        Answer the question accurately and clearly, providing any relevant details.
        """

        # Prepare request to Groq API
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        data = {
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "model": "mistral-saba-24b",
            "max_tokens": 200,
            "temperature": 0.7,
        }

        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Groq API error: {response.text}")

        # Parse and return the response
        chat_completion = response.json()
        answer = chat_completion["choices"][0]["message"]["content"].strip()

        return {"answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))