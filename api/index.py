from fastapi import FastAPI, File, UploadFile, HTTPException
import requests
import json
from datetime import datetime
import base64
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer
from TTS.api import TTS
import re
from pydub import AudioSegment
import simpleaudio as sa
import inflect


p = inflect.engine()

def convert_numbers_to_words(input_string):
    
    numbers = re.findall(r'\d+', input_string)
    
    
    for num in numbers:
        word = p.number_to_words(int(num))
        
        word = word.replace("-", " ")
        input_string = input_string.replace(num, word, 1)

    return input_string


text = "I have 3 apples and 21 bananas. I need 100 more."
result = convert_numbers_to_words(text)
print(result)


from supabase import create_client, Client
import numpy as np


url = "https://nrgavxxnufxbyolqznop.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5yZ2F2eHhudWZ4YnlvbHF6bm9wIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU4NDMyNjgsImV4cCI6MjA1MTQxOTI2OH0.ze2PsT5sVGgZsGAouEtgIf--JBWwwbvPhhcwSurF_pg"

app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")


tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", gpu=False)

AUDIO_SAVE_PATH = "input_audio.mp3"
ANSWER_PATH = "final_answer.wav"


class SummarizePayload(BaseModel):
    descriptions: List[str]  


class TranscriptPayload(BaseModel):
    transcript: str  

GROQ_API_KEY = "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"  

@app.get("/api/py/hi")
async def hi():
    
    answer = fetch_relevant_context("how are you")
    print(answer)
    return {"message": "hi"}


@app.post("/api/py/clone-voice")
async def clone_voice(audio: UploadFile = File(...)):
    """
    Endpoint to upload a voice sample, clone the voice, and generate cloned audio.
    """
    audio_path = AUDIO_SAVE_PATH
    with open(audio_path, "wb+") as f:
        f.write(await audio.read())

    return {
        "message": "Cloned voice generated successfully!"
    }

@app.post("/api/py/describe-image")
async def describe_image(image: UploadFile = File(...)):
    try:
        
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

        
        response = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=data)
        response.raise_for_status()

        
        chat_completion = response.json()
        parsed_content = json.loads(chat_completion['choices'][0]['message']['content'])
        description = parsed_content.get('description', 'No commentary generated.')

        
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

        
    response = supabase.rpc(
        "match_documents",
        {
            "query_embedding": question_embedding.tolist(),
            "match_threshold": 0.1,  
            "match_count": top_k          
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
        
        context_str = fetch_relevant_context(question)

        
        prompt = f"""
        You are an AI assistant. Answer the question accurately addressing the user directly using the following context.
        
        Context:
        {context_str}
        
        Question:
        {question}
        
        Answer the question accurately and clearly, providing any relevant details.
        """

        
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

        
        chat_completion = response.json()
        answer = chat_completion["choices"][0]["message"]["content"].strip()

        simple_answer = convert_numbers_to_words(answer)

        tts.tts_to_file(
            text=simple_answer,
            file_path=ANSWER_PATH,
            speaker_wav=["input_audio.mp3"],
            language="en"
        )

        print("Answer generated and saved as 'final_answer.wav'")

        
        audio = AudioSegment.from_wav("final_answer.wav")

        
        sa.play_buffer(
            audio.raw_data,
            num_channels=audio.channels,
            bytes_per_sample=audio.sample_width,
            sample_rate=audio.frame_rate,
        )


        return {"answer":answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

