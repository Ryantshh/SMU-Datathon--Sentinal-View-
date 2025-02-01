import os
import json
from tqdm import tqdm  # Progress bar library
from transformers import pipeline

# Load BERT NER pipeline
print("Loading BERT NER pipeline...")
ner_pipeline = pipeline(
    "ner",
    model="dbmdz/bert-large-cased-finetuned-conll03-english",
    aggregation_strategy="simple",
    device=0  # Use CPU (-1) or GPU (0 if available)
)
print("NER pipeline loaded.")

# Define relevant labels and confidence threshold
RELEVANT_LABELS = {"ORG", "PER"}
SCORE_THRESHOLD = 0.80

def extract_entities_bert(text, filename):
    """
    Extract entities using a BERT-based NER model.
    Handles and removes subword tokens (## prefixes).
    """
    entities = []
    ner_results = ner_pipeline(text)
    for result in ner_results:
        entity_text = result["word"].strip()

        # Skip subword tokens (those starting with ##)
        if entity_text.startswith("##"):
            continue

        # Clean up tokenization artifacts (join subwords)
        entity_text = entity_text.replace("##", "")

        # Add entity only if it passes filters
        if result["entity_group"] in RELEVANT_LABELS and result["score"] >= SCORE_THRESHOLD:
            entities.append({
                "text": entity_text,
                "label": result["entity_group"],
                "score": float(result["score"]),  # Convert score to standard float
                "filename": filename  # Add the source filename
            })
    return entities


def process_text_files(input_dir):
    """
    Process text files from a directory and extract entities.
    Adds filename to each extracted entity for traceability.
    Returns a list of all extracted entities.
    """
    all_entities = []
    text_files = [f for f in os.listdir(input_dir) if f.endswith("_text.txt")]
    
    # Use tqdm to show a progress bar
    for text_file in tqdm(text_files, desc="Processing files"):
        text_path = os.path.join(input_dir, text_file)
        
        # Read the text content
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract entities with filename included
        entities = extract_entities_bert(text, text_file)
        all_entities.extend(entities)
    return all_entities

def deduplicate_entities(entities):
    """
    Deduplicate entities based on both their 'text' and 'filename'.
    """
    seen = set()
    deduplicated = []
    for entity in tqdm(entities, desc="Deduplicating entities"):
        # Create a tuple of (text, filename) to check for duplicates
        key = (entity["text"], entity["filename"])
        if key not in seen:
            seen.add(key)
            deduplicated.append(entity)
    return deduplicated

if __name__ == "__main__":
    # Input directories
    pdf_text_dir = "../processed_data/wikileaks_texts"  # Path to extracted Wikileaks texts
    news_text_dir = "../processed_data/news_texts"  # Path to extracted News texts
    combined_entities_file = "../processed_data/combined_entities.json"  # Combined output file

    # Extract entities from PDFs
    print("Starting entity extraction for PDFs...")
    pdf_entities = process_text_files(pdf_text_dir)

    # Extract entities from News
    print("\nStarting entity extraction for News...")
    news_entities = process_text_files(news_text_dir)

    # Combine and deduplicate entities
    print("\nCombining and deduplicating entities...")
    all_entities = pdf_entities + news_entities
    deduplicated_entities = deduplicate_entities(all_entities)

    # Save deduplicated entities to a single JSON file
    with open(combined_entities_file, 'w', encoding='utf-8') as out_f:
        json.dump(deduplicated_entities, out_f, indent=4)
    print(f"All entities saved to: {combined_entities_file}")
