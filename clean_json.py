import json

# Path to the JSON file
input_file = "extracted_data.json"
output_file = "cleaned_data.json"

# Load the JSON data
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter out entries with empty content
cleaned_data = [entry for entry in data if entry.get("content", "").strip()]

# Save the cleaned data back to a new JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

print(f"Cleaned data saved to {output_file}")
