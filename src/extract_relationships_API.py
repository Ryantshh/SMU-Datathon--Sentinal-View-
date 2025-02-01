import json
import os
import re
import openai
import time
from collections import defaultdict
from nltk.tokenize import sent_tokenize
from tqdm import tqdm

# Set OpenAI API key
openai.api_key = "YOUR_API_KEY"

# File paths
input_json_file = "../processed_data/cleaned_filtered_entities.json"
output_file = "../processed_data/extracted_relationships.json"
news_dir = "../processed_data/news_texts"
wikileaks_dir = "../processed_data/wikileaks_texts"

# Define expected keys for validation
REQUIRED_KEYS = {"Entity 1", "Entity 2", "Relationship Summary", "Confidence Score", "Relevant Context", "Threat Assessment"}

def clean_relevant_context(text):
    """Cleans the relevant context text by removing unwanted Unicode characters."""
    cleaned_text = text.encode('utf-8').decode('unicode_escape')
    cleaned_text = re.sub(r'\\u[0-9a-fA-F]{4}', '', cleaned_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

def extract_relevant_sentences(text, entity1, entity2):
    """Extract sentences containing both entities or combine if no overlap."""
    sentences = sent_tokenize(text)
    sentences_with_entity1 = [s for s in sentences if re.search(rf"\b{re.escape(entity1)}\b", s, re.IGNORECASE)]
    sentences_with_entity2 = [s for s in sentences if re.search(rf"\b{re.escape(entity2)}\b", s, re.IGNORECASE)]
    sentences_with_both = [s for s in sentences_with_entity1 if s in sentences_with_entity2]

    return " ".join(sentences_with_both) if sentences_with_both else " ".join(sentences_with_entity1 + sentences_with_entity2)

def validate_json_response(parsed_result):
    """Validates that the parsed JSON contains the required keys."""
    if not isinstance(parsed_result, dict):
        return False
    missing_keys = REQUIRED_KEYS - parsed_result.keys()
    if missing_keys:
        print("Validation Error: Missing keys in response:", missing_keys)
        return False
    return True

def extract_relationship(entity1, entity2, text):
    """Extract relationships using OpenAI's API with retries and error handling."""
    while True:
        try:
            # Define system and user prompts
            system_prompt = """
You will be provided with two entities and related text. Your task is to extract their relationship and provide a valid JSON response.

---

### **Response Format**
The JSON should include the following fields. Ensure no null or unknown values are returned:

1. **Entity 1**:  
   - Name of the first entity in the input.  
   - Example: "Entity_A"

2. **Entity 2**:  
   - Name of the second entity in the input.  
   - Example: "Entity_B"

3. **Relationship Summary**:  
   - A concise summary of the relationship between Entity 1 and Entity 2.  
   - Example: "Entity_A collaborated with Entity_B on data breaches."

4. **Confidence Score**:  
   - Confidence in the relationship summary (0% - 100%).  
   - Example: "90%"

5. **Relevant Context**:  
   - Text snippet supporting the relationship summary.  
   - Example: "Entity_A collaborated with Entity_B to conduct sensitive operations involving data breaches."

6. **Threat Assessment**:  
   - Analysis of any national security threat related to the relationship:  
     - **Threat Level**: Value between 1 (low) and 10 (high).  
       - Example: 8  
     - **Type**: Category of threat.  
       - Example: "Cybersecurity"  
     - **Explanation**: Explanation of the threat based on the context.  
       - Example: "The collaboration involved data breaches, indicating a cybersecurity threat."  
     - **Impact level on Singapore**: Value between 1 (low) and 10 (high).  
       - Example: 0  
     - **Explanation (Singapore)**: Explanation of how the threat impacts Singapore.  
       - Example: "There is no direct threat to Singapore."

7. **Origin Location 1**:  
   - Location associated with Entity 1, inferred from the text.  
   - Example: "New York"

8. **Origin Location 2**:  
   - Location associated with Entity 2, inferred from the text.  
   - Example: "London"

---

### **Example Input**:
Entity 1: Entity_A  
Entity 2: Entity_B  
Text: Entity_A collaborated with Entity_B to conduct sensitive operations that involved data breaches. Entity_A was based in New York, while Entity_B was from London.

---

### **Example JSON Output**:
{
    "Entity 1": "Entity_A",
    "Entity 2": "Entity_B",
    "Relationship Summary": "Entity_A collaborated with Entity_B on sensitive operations involving data breaches.",
    "Confidence Score": "90%",
    "Relevant Context": "Entity_A collaborated with Entity_B to conduct sensitive operations that involved data breaches.",
    "Threat Assessment": {
        "Threat Level": 8,
        "Type": "Cybersecurity",
        "Explanation": "The collaboration involved data breaches, indicating a cybersecurity threat.",
        "Impact level on Singapore": 0,
        "Explanation (Singapore)": "There is no direct threat to Singapore."
    },
    "Origin Location 1": "New York",
    "Origin Location 2": "London"
}

---

### **Important Instructions**:
- Return **only** the JSON response.  
- Ensure the JSON response is **well-structured** and **valid**.
- Do not include any additional text, explanations, or comments outside the JSON.

            """

            user_prompt = (
                f"Entity 1: {entity1}\n"
                f"Entity 2: {entity2}\n"
                f"Text: {text}\n"
                "Result:\nPlease provide a JSON response."
            )

            # Make the API call to OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )

            # Extract the raw response content
            raw_result = response["choices"][0]["message"]["content"].strip()
            print("Raw Result Content:", raw_result)

            # Ensure the response is valid JSON
            parsed_result = json.loads(raw_result)

            if not validate_json_response(parsed_result):
                print("Error: Response does not meet the expected structure.")
                continue  # Retry if validation fails

            return parsed_result

        except (json.JSONDecodeError, openai.error.APIError) as e:
            print(f"Error occurred: {str(e)}. Retrying...")
            time.sleep(5)

def append_to_json(result, output_path):
    """Append a single result to the JSON file."""
    if not os.path.exists(output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([result], f, indent=4)
    else:
        with open(output_path, "r+", encoding="utf-8") as f:
            f.seek(0, 2)
            file_size = f.tell()

            if file_size > 2:
                f.seek(file_size - 1)
                f.truncate()
                f.write(",\n")

            json.dump(result, f, indent=4)
            f.write("\n]")

def finalize_json(output_path):
    """Ensure the JSON file ends with a proper closing bracket."""
    with open(output_path, "r+", encoding="utf-8") as f:
        f.seek(0, 2)
        file_size = f.tell()

        if file_size > 2:
            f.seek(file_size - 2)
            if f.read(1) != "]":
                f.write("\n]")

if __name__ == "__main__":
    with open(input_json_file, "r", encoding="utf-8") as f:
        entities = json.load(f)

    grouped_entities = defaultdict(list)
    for entity in entities:
        grouped_entities[entity["filename"]].append(entity["text"])

    for filename, entity_list in tqdm(grouped_entities.items(), desc="Processing files"):
        file_path = os.path.join(news_dir if filename.startswith("news_row") else wikileaks_dir, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            continue

        entity_pairs = [(entity1, entity2) for i, entity1 in enumerate(entity_list) for entity2 in entity_list[i + 1:] if entity1 != entity2]

        for entity1, entity2 in entity_pairs:
            relevant_text = extract_relevant_sentences(text, entity1, entity2)

            if not relevant_text.strip():
                continue

            result = extract_relationship(entity1, entity2, relevant_text)
            append_to_json(result, output_file)

    finalize_json(output_file)
    print(f"Results saved progressively to {output_file}.")
