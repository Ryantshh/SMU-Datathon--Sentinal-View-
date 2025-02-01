import json
import torch
import re
import os
from tqdm import tqdm
from collections import defaultdict
from nltk.tokenize import sent_tokenize
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

print(torch.version.cuda)  # Should match your installed CUDA version
print(torch.backends.cudnn.version()) 
# Load Hugging Face Model (Replace with your DeepSeek-R1-Distill model)
MODEL_NAME = "deepseek-ai/deepseek-r1-distill-qwen-7b"
# Enable 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,  
    bnb_4bit_compute_dtype=torch.float16,  
    bnb_4bit_use_double_quant=True,  
    bnb_4bit_quant_type="nf4"
)

print("🔄 Loading Model...")
try:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map=0,
        max_memory={"cuda": "6GB", "cpu": "8GB"},  # Prevents out-of-memory errors
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = torch.compile(model)

    print("✅ Model loaded successfully!")

    # Debug: Check if uint8 issue still exists
    for name, param in model.named_parameters():
        print(f"{name}: {param.dtype}")  # Should print "torch.float16"

except Exception as e:
    print(f"❌ Model loading failed: {e}")
    exit()

# File Paths
input_json_file = "../processed_data/cleaned_filtered_entities.json"
wikileaks_dir = "../processed_data/wikileaks_texts"
news_dir = "../processed_data/news_texts"
output_file = "../processed_data/final_extracted_relationships2.json"


# Clean Relevant Context
def clean_relevant_context(text):
    cleaned_text = text.encode('utf-8').decode('unicode_escape')
    cleaned_text = re.sub(r'\\u[0-9a-fA-F]{4}', '', cleaned_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text


# Extract Relevant Sentences
def extract_relevant_sentences(text, entity1, entity2):
    sentences = sent_tokenize(text)
    sentences_with_entity1 = [s for s in sentences if re.search(rf"\b{re.escape(entity1)}\b", s, re.IGNORECASE)]
    sentences_with_entity2 = [s for s in sentences if re.search(rf"\b{re.escape(entity2)}\b", s, re.IGNORECASE)]
    sentences_with_both = [s for s in sentences_with_entity1 if s in sentences_with_entity2]

    if sentences_with_both:
        return " ".join(sentences_with_both)
    return " ".join(sentences_with_entity1 + sentences_with_entity2)


# Extract Relationship Using Local Model (No Batch Processing)
def extract_relationship(entity1, entity2, text):
    """
    Uses a local Hugging Face model to extract relationships for a single entity pair.
    """
    try:
        # Exact System Prompt (No Changes)
        system_prompt = """
            You will be provided with two entities and related text. Your task is to extract their relationship and provide a JSON response.

            The JSON should include the following fields:
            1. "Entity 1": The first entity provided in the input.
            2. "Entity 2": The second entity provided in the input.
            3. "Relationship Summary": A concise summary of the relationship between Entity 1 and Entity 2, based on the given text.
            4. "Confidence Score": A numerical score (in percentage, 0-100%) indicating your confidence in the relationship summary.
            5. "Relevant Context": A short snippet of text from the input that supports the relationship summary.
            6. "Threat Assessment":
                - "Threat Level": A numerical threat level from 1 (low threat) to 10 (high threat), this shows the potential impact of the threat.
                - "Type": A concise label for the type of threat (e.g., "Cybersecurity", "Espionage", "Economic", "Diplomatic", "Terrorism", "Military", "Disinformation", "Environmental", "Organized Crime", "Biological", "Chemical", "Nuclear", "Energy", "Geopolitical", "Critical Infrastructure", "Ideological", "Insider Threats", "Social Unrest", "Supply Chain", "Human Trafficking", "Financial Fraud", "Weapon Proliferation", "Border Security", "Religious Extremism", "Narco-Terrorism", "Space Security", "Maritime Security", "Artificial Intelligence Abuse", "Satellite Disruption", "Propaganda", "Intellectual Property Theft", "Cultural Sabotage").
                - "Explanation": A short explanation of the threat level and type based on the context.
                - "Impact level on Singapore": A numerical impact level on Singapore from 1 (low impact) to 10 (high impact)
                - "Explaination(Singaopre): A short explaination of how the threat impacts Singapore if it doesnt set it as 0"
            7. "Origin Location 1": The origin location of Entity 1, if it can be inferred from the text. If cannot be inferred from text, infer the location yourslef no null values or unknown values allowed.
            8. "Origin Location 2": The origin location of Entity 2, if it can be inferred from the text. If cannot be inferred from text, infer the location yourslef no null values or unknown values allowed
            EXAMPLE INPUT:
            Entity 1: Entity_A
            Entity 2: Entity_B
            Text: Entity_A collaborated with Entity_B to conduct sensitive operations that involved data breaches. Entity_A was based in New York, while Entity_B was from London.

            EXAMPLE JSON OUTPUT:
            {
                "Entity 1": "Entity_A",
                "Entity 2": "Entity_B",
                "Relationship Summary": "Entity_A collaborated with Entity_B on sensitive operations involving data breaches.",
                "Confidence Score": "90%",
                "Relevant Context": "Entity_A collaborated with Entity_B to conduct sensitive operations that involved data breaches.",
                "Threat Assessment": {
                    "Level": 8,
                    "Type": "Cybersecurity",
                    "Explanation": "The collaboration involved data breaches, indicating a high cybersecurity threat.",
                    "Impact level on Singapore": 0,
                    "Explaination(Singapore)":"There is no direct threat to Singapore"
                },
                "Origin Location 1": "New York",
                "Origin Location 2": "London"
            }
            """

        # Format input to mimic OpenAI's chat format manually
        
        formatted_prompt = f"""
        ### System Instructions:
        {system_prompt}

        ### User Input:
        Entity 1: {entity1}
        Entity 2: {entity2}
        Text: {text}

        ### Expected JSON Output(Summarize within 300 tokens and your output should only include the JSON OUTPUT):
        """

        # Tokenize and run inference
        inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
        # Generate output
        with torch.no_grad():
            output = model.generate(
                    **inputs,
                    max_new_tokens=1000,  # ✅ Allow enough tokens for complete JSON
                    # temperature=0.3,  # ✅ Reduce randomness for structured responses
                    # top_p=0.8,  # ✅ Focus on high-probability outputs
                    # repetition_penalty=1.2,  # ✅ Prevent repeating phrases
                    pad_token_id=tokenizer.eos_token_id    )

        # Decode output
        response_text = tokenizer.decode(output[0], skip_special_tokens=True)
        print(response_text)
        # Extract JSON response
        json_match = re.search(r"\{.*?\}", response_text, re.DOTALL)
        if json_match:
            parsed_result = json.loads(json_match.group())
            if "Relevant Context" in parsed_result:
                parsed_result["Relevant Context"] = clean_relevant_context(parsed_result["Relevant Context"])
            print(parsed_result)
            return parsed_result

    except Exception as e:
        return {"Entity 1": entity1, "Entity 2": entity2, "Error": str(e)}

    return {}


# Initialize JSON Output File
def initialize_json(output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("[\n]")  # Start with an empty JSON array


# Append Results to JSON File Progressively
def append_to_json(result, output_path, first_result=False):
    with open(output_path, "r+", encoding="utf-8") as f:
        f.seek(0, 2)
        file_size = f.tell()

        if file_size > 2:
            f.seek(file_size - 2)
            f.truncate()
            if not first_result:
                f.write(",\n")

        json.dump(result, f, indent=4, ensure_ascii=False)
        f.write("\n]")


# Finalize JSON File
def finalize_json(output_path):
    with open(output_path, "r+", encoding="utf-8") as f:
        f.seek(0, 2)
        file_size = f.tell()
        if file_size > 2:
            f.seek(file_size - 2)
            if f.read(1) != "]":
                f.write("\n]")


# Main Execution
if __name__ == "__main__":
    initialize_json(output_file)

    with open(input_json_file, "r", encoding="utf-8") as f:
        entities = json.load(f)

    grouped_entities = defaultdict(list)
    for entity in entities:
        grouped_entities[entity["filename"]].append(entity["text"])

    first_result = True
    for filename, entity_list in tqdm(grouped_entities.items(), desc="Processing files"):
        file_path = os.path.join(news_dir, filename) if filename.startswith("news_row") else os.path.join(wikileaks_dir, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            continue

        entity_pairs = [(e1, e2) for i, e1 in enumerate(entity_list) for e2 in entity_list[i + 1:] if e1 != e2]

        for entity1, entity2 in entity_pairs:
            relevant_text = extract_relevant_sentences(text, entity1, entity2)

            if not relevant_text.strip():
                continue

            result = extract_relationship(entity1, entity2, relevant_text)
            append_to_json(result, output_file, first_result)
            first_result = False

    finalize_json(output_file)
    print(f"Results saved progressively to {output_file}.")