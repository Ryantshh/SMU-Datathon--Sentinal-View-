import json
import unicodedata


def is_acronym(full_form, acronym):
    """
    Check if a string is an acronym of the given full form.
    Args:
        full_form (str): Full-form text (e.g., "Ministry of Foreign Affairs").
        acronym (str): Acronym to check (e.g., "MFA").
    Returns:
        bool: True if the acronym matches the full form, False otherwise.
    """
    # Build an acronym from the first letters of capitalized words in the full form
    full_form_letters = "".join([word[0] for word in full_form.split() if word[0].isupper()])
    return full_form_letters == acronym


def filter_redundant_entities(entities):
    """
    Remove acronyms from the list if their full forms exist.
    Args:
        entities (list): List of entities to filter.
    Returns:
        tuple: Filtered list of entities and set of removed acronyms.
    """
    filtered_entities = []
    acronyms = set()

    for entity in entities:
        text = entity["text"]
        # Check if this entity is an acronym of any other entity in the list
        if any(is_acronym(other_entity["text"], text) for other_entity in entities if other_entity != entity):
            acronyms.add(text)
        else:
            filtered_entities.append(entity)
    
    return filtered_entities, acronyms


def clean_entities(entities, score_threshold=0.80):
    """
    Clean the extracted entities by:
    - Removing single-character entities for all labels.
    - Removing single-word entities only for PER labels.
    - Removing low-confidence entities.
    - Removing Unicode artifacts (e.g., combining characters).
    - Prioritizing longer entities over shorter partial duplicates.
    """
    cleaned_entities = []
    seen = set()

    for entity in entities:
        # Skip entities with low scores
        if entity["score"] < score_threshold:
            print(f"Skipping entity due to low score: {entity}")
            continue

        # Normalize Unicode to composed form (NFC)
        normalized_text = unicodedata.normalize("NFC", entity["text"]).strip()

        # Skip single-character entities (all labels)
        if len(normalized_text) < 2:
            print(f"Skipping single-character entity: {entity}")
            continue

        # Skip single-word entities only for PER labels
        if entity["label"] == "PER" and " " not in normalized_text:
            print(f"Skipping single-word PER entity: {entity}")
            continue

        # Deduplicate based on normalized text
        key = normalized_text.lower()
        if key not in seen:
            # Handle partial duplicates: Keep the longer entity
            should_add = True
            for existing_entity in cleaned_entities:
                existing_text = unicodedata.normalize("NFC", existing_entity["text"]).strip().lower()
                if key in existing_text or existing_text in key:
                    # Replace shorter entity with the longer one
                    if len(key) > len(existing_text):
                        print(f"Replacing shorter entity: {existing_entity} with {entity}")
                        cleaned_entities.remove(existing_entity)
                        seen.remove(existing_text)
                    else:
                        should_add = False
                    break

            if should_add:
                seen.add(key)
                entity["text"] = normalized_text  # Update the entity with cleaned text
                cleaned_entities.append(entity)

    return cleaned_entities


if __name__ == "__main__":
    # Define file paths
    input_file = "../processed_data/combined_entities.json"  # Path to input file with entities
    output_file = "../processed_data/cleaned_filtered_entities.json"  # Path to save final cleaned and filtered entities

    # Load the entities from the JSON file
    print(f"Loading entities from: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        entities = json.load(f)

    # Step 1: Clean entities
    print("Cleaning entities...")
    cleaned_entities = clean_entities(entities)

    # Step 2: Filter redundant acronyms
    print("Filtering redundant acronyms...")
    filtered_entities, removed_acronyms = filter_redundant_entities(cleaned_entities)

    # Save the cleaned and filtered entities to a new file
    print(f"Saving cleaned and filtered entities to: {output_file}")
    with open(output_file, "w", encoding="utf-8") as out_f:
        json.dump(filtered_entities, out_f, indent=4, ensure_ascii=False)

    # Log the removed acronyms
    print(f"Removed acronyms: {removed_acronyms}")
    print(f"Cleaned and filtered entities saved to: {output_file}")
