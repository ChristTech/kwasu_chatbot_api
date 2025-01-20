from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Initialize FastAPI app
app = FastAPI()

# Load the model and tokenizer
model_name = "meta-llama/Llama-2-7b-hf"  # Replace with the model you've tested
device = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype=torch.float16)
model.to(device)
print("Model loaded!")

# Define request and response schema
class QueryRequest(BaseModel):
    context: str
    question: str

class QueryResponse(BaseModel):
    answer: str

@app.get("/")
def home():
    return {"message": "Welcome to the Llama-2 API. Use the /generate endpoint to ask questions."}

@app.post("/generate", response_model=QueryResponse)
def generate_answer(request: QueryRequest):
    try:
        # Construct the prompt
        prompt = f"Context: {request.context}\nQuestion: {request.question}\nAnswer:"
        
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt").to(device)

        # Generate output
        outputs = model.generate(inputs["input_ids"], max_new_tokens=100, do_sample=True, top_p=0.9)
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract and return the response
        return {"answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
