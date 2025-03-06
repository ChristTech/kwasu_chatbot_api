import requests
import json

import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from openai import OpenAI

# Load FAISS index once
index = faiss.read_index("faiss_index.bin")

# token = os.environ["GITHUB_TOKEN"]
# endpoint = "https://models.inference.ai.azure.com"
# model_name = "gpt-4o"

# client = OpenAI(
#     base_url=endpoint,
#     api_key=token,
# )


# # Load chunks once
# with open('temp_documents.txt', 'r', encoding='utf-8') as file:
#     chunks = [chunk.strip() for chunk in file.read().split("\n\n") if chunk.strip()]

# # Load embedding model once
# embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')

# def get_context(query, top_k=1):  # Reduce top_k to 1 or 2
#     """
#     Retrieves relevant chunks based on the query, limiting text length for efficiency.

#     Args:
#         query (str): The user's question.
#         top_k (int): Number of relevant chunks to retrieve.
#         max_sentences (int): Maximum number of sentences to return from each chunk.

#     Returns:
#         str: Concise relevant context.
#     """

#     query_embedding = embedding_model.encode([query]).astype('float32')
#     distances, indices = index.search(query_embedding, top_k)

#     # Get unique non-empty chunks
#     retrieved_chunks = list(set(chunks[i].strip() for i in indices[0] if chunks[i].strip()))

#     context = "\n".join(retrieved_chunks[:1])  # Limit to 1-2 chunks
#     return f'"""\n{context}\n"""' if context else '"""\nNo relevant information found.\n"""'

# # Function to check if the retrieved context is meaningful
# def is_context_valid(context):
#     """Returns True if the context contains meaningful information."""
#     word_count = len(context.split())
#     return word_count > 5 and len(context) > 50  # Ensures it has at least a sentence

# Example usage
# print(get_context("Who is the vice chancellor of KWASU?"))



# # API endpoint
# url = "https://openrouter.ai/api/v1/chat/completions"

# # Your API token
# api_token = "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"  # Replace with your actual token

# # Request headers
# headers = {
#     "Authorization": f"Bearer {api_token}",
#     "Content-Type": "application/json"
# }


# while True:
#     query = input("Enter a query: ")
#     context = get_context(query)

#     if not is_context_valid(context):
#         print("⚠️ Context is too vague. Defaulting to model's general knowledge.")
#         context = ""

#     data = {
#         "model": "deepseek/deepseek-r1",
#         "messages": [
#             # {"role": "system", "content": "You are an expert assistant providing factual answers."},
#             {"role": "user", "content": f"Context: {context}\nQuestion: {query}"}
#         ]
#     }

#     print(f"🔍 Context being sent:\n{context}")

#     try:
#         response = requests.post(url, headers=headers, data=json.dumps(data))
#         response.raise_for_status()

#         if response.status_code == 200:
#             result = response.json()
            
#             # Extract content safely
#             choices = result.get("choices", [{}])
#             if choices:
#                 message = choices[0].get("message", {})
#                 answer = message.get("content", "").strip()

#                 if not answer:  # If empty, provide a fallback response
#                     answer = "I'm sorry, I couldn't find an answer. Let me know if I should try again!"

#                 print("📝 Answer:", answer)
#             else:
#                 print("⚠️ No choices returned. Unable to generate an answer.")
#         else:
#             print(f"❌ Error: {response.status_code} - {response.text}")
#     except requests.exceptions.RequestException as e:
#         print(f"🚨 API request failed: {e}")

from groq import Groq
#while True:

    # query = input('Enter a query: ')
    # context = get_context(query)
    # print(context)

    # if not is_context_valid(context):
    #     print("⚠️ Context is too vague. Defaulting to model's general knowledge.")
    #     context = ""

import requests
import json

API_KEY = os.getenv("GROQ_API_KEY") # Replace with your actual API key

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "mixtral-8x7b-32768",  # Use Mixtral for best performance
    "messages": [
        {"role": "system", "content": "You are a helpful AI assistant that only gives answers to questions about kwara state university, nothing else."},
        {"role": "user", "content": "Where is the eiffel tower located?"}
    ],
    "temperature": 0.7
}

response = requests.post(url, headers=headers, data=json.dumps(data))
result = response.json()

print(response.choices[0].message.content)

