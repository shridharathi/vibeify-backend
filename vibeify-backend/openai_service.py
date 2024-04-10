import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
from utils import encode_image

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_EMBEDDING_MODEL = 'text-embedding-ada-002'
CHATGPT_MODEL = 'gpt-4-vision-preview'


def get_embedding(chunk):
  url = 'https://api.openai.com/v1/embeddings'
  headers = {
      'content-type': 'application/json; charset=utf-8',
      'Authorization': f"Bearer {OPENAI_API_KEY}"            
  }
  data = {
      'model': OPENAI_EMBEDDING_MODEL,
      'input': chunk
  }
  response = requests.post(url, headers=headers, data=json.dumps(data))  
  response_json = response.json()
  embedding = response_json["data"][0]["embedding"]
  return embedding


def call_gpt(prompt):
  messages = [{"role": "system", "content": "You are a helpful assistant."}]
  messages.append({"role": "user", "content": prompt})
  url = 'https://api.openai.com/v1/chat/completions'

  headers = {
      'content-type': 'application/json; charset=utf-8',
      'Authorization': f"Bearer {OPENAI_API_KEY}"            
  }
  data = {
      'model': CHATGPT_MODEL,
      'messages': messages,
      'temperature': 1, 
      'max_tokens': 1000
  }
  try:
    response = requests.post(url, headers=headers, json=data)  # Using json=data to automatically set content-type
    response.raise_for_status()  # This will raise an exception for HTTP error codes

    # If you want to print the response text every time, uncomment the next line

    response_json = response.json()
    completion = response_json["choices"][0]["message"]["content"]
    return completion
  except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}\nResponse Text: {response.text}")
  except Exception as err:
    print(f"An error occurred: {err}")
  return None

#"Output a playlist of only 5 songs which match the mood of the image only in this format: '"Song" - Artist'; NO EXTRA TEXT. Each artist must be different. Only output the song titles and artists — no descriptions. Don't number the list."
def call_gpt_with_image(img):
  messages = [{"role": "system", "content": "You are a helpful assistant."}]
  prompt = "Output a playlist of only 5 songs which match the mood of the image, each song in this format: \"Song\" - Artist; NO EXTRA TEXT. Each artist must be different."
  messages.append(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img}"},
                },
            ],
        }
    )
  url = 'https://api.openai.com/v1/chat/completions'

  headers = {
      'content-type': 'application/json; charset=utf-8',
      'Authorization': f"Bearer {OPENAI_API_KEY}"            
  }
  data = {
      'model': CHATGPT_MODEL,
      'messages': messages,
      'temperature': 1, 
      'max_tokens': 1000
  }
  try:
    response = requests.post(url, headers=headers, json=data)  # Using json=data to automatically set content-type
    response.raise_for_status()  # This will raise an exception for HTTP error codes

    # If you want to print the response text every time, uncomment the next line

    response_json = response.json()
    completion = response_json["choices"][0]["message"]["content"]
    return completion
  except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}\nResponse Text: {response.text}")
  except Exception as err:
    print(f"An error occurred: {err}")
  return None


