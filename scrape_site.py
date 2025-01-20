# Function to read the large text file
def read_large_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        # Read the file line by line (or you can read in chunks)
        text = file.read()
    return text

# Example usage
file_path = 'temp_documents.txt'
scraped_text = read_large_file(file_path)

print("Loaded Text Length:", len(scraped_text))  # Check how large the text is


import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Function to segment the text into sentences
def segment_text(text):
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]  # Segment into sentences
    return sentences

# Example usage
sentences = segment_text(scraped_text)

print("Number of Sentences:", len(sentences))  # Check how many sentences were segmented


# Function to extract named entities from the text
def extract_entities(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities

# Example usage
entities = extract_entities(scraped_text)

print("Extracted Entities:", entities)


