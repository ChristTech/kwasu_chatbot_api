import requests
import json

# API endpoint
url = "https://openrouter.ai/api/v1/chat/completions"

# Your API token
api_token = ""  # Replace with your actual token

# Request headers
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# Context and Query
context = """
Kwara State University (KWASU) is a state-owned institution in Nigeria. It has several campuses dedicated to diverse fields of study.
- Main Campus: Malete
- Osi Campus: Focus on Agriculture
- Ilesha-Baruba Campus: Focus on Education
"""
query = "How many campuses does Kwara State University have?"

# Request payload
data = {
    "model": "google/gemini-2.0-flash-thinking-exp:free",  # Optional: Specify model
    "messages": [
        {"role": "system", "content": "You are an expert assistant providing factual answers based on the given context."},
        {"role": "user", "content": f"Context: {context}\nQuestion: {query}"}
    ]
}

# Send the POST request
try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()  # Raise an HTTPError for bad responses

    # Parse the response
    if response.status_code == 200:
        result = response.json()
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        print("Answer:", answer.strip())  # Print only the assistant's answer
    else:
        print(f"Error: {response.status_code} - {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
