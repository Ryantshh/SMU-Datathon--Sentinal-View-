import json

def clean_values(record):
    """
    Recursively updates values in the record if they are "", "Unknown", or "N/A" to None.
    """
    for key, value in record.items():
        if isinstance(value, dict):
            clean_values(value)  # Recursively clean nested dictionaries
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    clean_values(item)  # Recursively clean nested lists of dictionaries
        else:
            # Replace invalid values with None
            if value in ["", "Unknown", "N/A"]:
                record[key] = None

def clean_json_data(input_file, output_file):
    """
    Reads the input JSON file, cleans the values, and writes the updated data to the output file.

    Args:
    - input_file: Path to the input JSON file.
    - output_file: Path to the output cleaned JSON file.
    """
    try:
        # Load the input JSON data
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Clean each entry in the data
        for entry in data:
            clean_values(entry)

        # Write the cleaned data to the output JSON file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"Cleaned JSON file saved to: {output_file}")

    except Exception as e:
        print(f"Error processing file: {e}")

# File paths
input_file = "../processed_data/extracted_relationships.json"
output_file = "../processed_data/cleaned_extracted_relationships.json"

# Run the cleaning script
clean_json_data(input_file, output_file)
