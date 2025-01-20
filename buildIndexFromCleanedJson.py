from llama_index.core import SimpleDirectoryReader


import json

# Path to your cleaned data
cleaned_data_path = "cleaned_data.json"

# Load the cleaned data
with open(cleaned_data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert JSON data into plain text format for indexing
documents = []
for entry in data:
    #title = entry.get("title", "No Title")
    content = entry.get("content", "")
    documents.append(f"Content: {content}")

# Save documents to a temporary text file
with open("temp_documents.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(documents))

# Use SimpleDirectoryReader to load the text data
documents = SimpleDirectoryReader(input_dir=".", input_files=["temp_documents.txt"]).load_data()


# # model_name = "gpt2"
# # tokenizer = AutoTokenizer.from_pretrained(model_name)
# # model = AutoModelForCausalLM.from_pretrained(model_name)

# # # Set up the LLM with the model and tokenizer
# # llm = HuggingFaceLLM(model=model, tokenizer=tokenizer)

# # # Set up local embedding model (HuggingFace)
# # Settings.embed_model = HuggingFaceEmbedding(
# #     model_name="BAAI/bge-small-en-v1.5"
# # )

# # Settings.llm = llm

# # # Create a vector index
# # index = VectorStoreIndex.from_documents(documents)

# # # Save the index for later use
# # index.storage_context.persist(persist_dir="kwasu_index_storage")

# # print("Indexing complete!")



# from sentence_transformers import SentenceTransformer
# import faiss
# import os

# # Load the sentence transformer model
# model = SentenceTransformer('BAAI/bge-small-en-v1.5')

# # Path to your .txt file
# file_path = 'temp_documents.txt'

# # Read the content of the file
# if os.path.exists(file_path):
#     with open(file_path, 'r', encoding='utf-8') as file:
#         content = file.read()
# else:
#     raise FileNotFoundError(f"The file '{file_path}' does not exist.")

# # Split content into chunks (e.g., paragraphs or sentences)
# chunks = content.split("\n\n")  # Split by double newline for paragraphs
# chunks = [chunk.strip() for chunk in chunks if chunk.strip()]  # Remove empty chunks
# print(f"Total chunks: {len(chunks)}")


# # Generate embeddings for each chunk
# embeddings = model.encode(chunks, show_progress_bar=True)

# # Convert embeddings to a FAISS-friendly format
# embeddings = embeddings.astype('float32')  # FAISS requires float32


# # Initialize the FAISS index
# dimension = embeddings.shape[1]  # Dimension of the embeddings
# index = faiss.IndexFlatL2(dimension)  # L2 distance is commonly used

# # Add embeddings to the index
# index.add(embeddings)

# print(f"Number of items in index: {index.ntotal}")



# # Example query
# query = "Who is the vice chancellor of KWASU?"

# # Generate embedding for the query
# query_embedding = model.encode([query]).astype('float32')

# # Perform a search
# k = 5  # Number of nearest neighbors to retrieve
# distances, indices = index.search(query_embedding, k)

# # Display results
# print("\nTop results:")
# for i in range(k):
#     print(f"Chunk: {chunks[indices[0][i]]}\nDistance: {distances[0][i]}")


# # Save the index
# faiss.write_index(index, "faiss_index.bin")

# # Load the index
# index = faiss.read_index("faiss_index.bin")
