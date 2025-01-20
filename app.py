from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
from transformers.utils import logging
import os

os.environ["TRANSFORMERS_CACHE"] = "/tmp/huggingface"
logging.set_verbosity_error()


app = FastAPI()

# Define a request body model
class QueryRequest(BaseModel):
    context: str
    question: str

# Global variables for the tokenizer and model
tokenizer = None
model = None

@app.on_event("startup")
async def load_model():
    """
    Dynamically load the LLaMA-2 model with 4-bit quantization for memory efficiency.
    """
    global tokenizer, model
    model_name = "meta-llama/Llama-2-7b-hf"

    # Configure Bits and Bytes for 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype="float16",
        bnb_4bit_use_double_quant=True,
    )

    # Load the tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Load the model with 4-bit quantization
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    print("Model loaded successfully with 4-bit quantization!")

@app.post("/generate")
async def generate_response(request: QueryRequest):
    """
    Generate a response based on the provided context and question.
    """
    global tokenizer, model
    if tokenizer is None or model is None:
        raise HTTPException(status_code=500, detail="Model not loaded yet!")

    # Prepare the input prompt
    max_context_length = 512  # Limit input tokens for memory efficiency
    context = request.context[:max_context_length]  # Truncate context if too long
    prompt = f"Context: {context}\nQuestion: {request.question}\nAnswer:"

    # Tokenize and generate a response
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
    outputs = model.generate(inputs["input_ids"], max_new_tokens=100, do_sample=True, top_p=0.9)

    # Decode and return the response
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"answer": answer}
