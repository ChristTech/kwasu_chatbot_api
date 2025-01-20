from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer
import faiss

# Load FAISS index
index = faiss.read_index("faiss_index.bin")

# Reload chunks from text
file_path = 'temp_documents.txt'
with open(file_path, 'r', encoding='utf-8') as file:
    chunks = [chunk.strip() for chunk in file.read().split("\n\n") if chunk.strip()]

# Load Sentence-Transformer model for embeddings
embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')

# Load a free conversational language model
model_name = "EleutherAI/gpt-neo-1.3B"  # Free and open-source
tokenizer = AutoTokenizer.from_pretrained(model_name)
chat_model = AutoModelForCausalLM.from_pretrained(model_name)

def chatbot_response(query, top_k=3):
    # Step 1: Encode query and retrieve chunks from FAISS
    query_embedding = embedding_model.encode([query]).astype('float32')
    distances, indices = index.search(query_embedding, top_k)
    retrieved_chunks = [chunks[i] for i in indices[0]]
    context = "\n".join(retrieved_chunks)

    # Step 2: Generate response using the chatbot model
    prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    outputs = chat_model.generate(inputs["input_ids"], max_length=300, num_return_sequences=1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return response

# Test the chatbot
query = "Who is the vice chancellor of KWASU?"
response = chatbot_response(query)
print(response)
