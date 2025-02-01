import os
import pdfplumber
import pandas as pd

# Extract text from each PDF file
def extract_text_from_pdfs(pdf_dir, output_dir):
    """Extract and save text from each PDF file."""
    os.makedirs(output_dir, exist_ok=True)
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith(".pdf"):
            print(f"Processing PDF: {pdf_file}")
            pdf_path = os.path.join(pdf_dir, pdf_file)
            output_file = os.path.join(output_dir, f"{os.path.splitext(pdf_file)[0]}_text.txt")
            with pdfplumber.open(pdf_path) as pdf:
                text = []
                for page in pdf.pages:
                    text.append(page.extract_text())
            # Save the text
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(text))
    print("PDF text extraction completed.")

def extract_text_from_wikileaks_grouped(wikileaks_file, output_dir):
    """Group rows by unique labels in the 'PDF Path' column and extract combined text."""
    os.makedirs(output_dir, exist_ok=True)

    # Load the Excel file
    df = pd.read_excel(wikileaks_file)

    # Correct column names
    label_column = "PDF Path"  # Column with labels like '1.pdf', '10.pdf'
    content_column = "Text"  # Column with the actual text content

    # Check if the required columns exist
    if label_column not in df.columns:
        raise KeyError(f"Column '{label_column}' not found in the Excel file.")
    if content_column not in df.columns:
        raise KeyError(f"Column '{content_column}' not found in the Excel file.")

    # Group rows by the 'PDF Path' column
    grouped = df.groupby(label_column)

    # Process each group
    for label, group in grouped:
        print(f"Processing group for label: {label}")

        # Combine all text from the 'Text' column for the current group
        combined_text = " ".join(group[content_column].dropna())

        # Save the combined text to a file named after the label
        output_file = os.path.join(output_dir, f"{label}_text.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(combined_text)

    print("Wikileaks text extraction completed.")

# Extract text from each row in the News Excel file
def extract_text_from_news(news_file, output_dir):
    """Extract and save text from each row in News data."""
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_excel(news_file)

    # Correct column name
    content_column = "Text"  # Replace 'Text' with the actual column name from the file

    # Check if the required column exists
    if content_column not in df.columns:
        raise KeyError(f"Column '{content_column}' not found in the News file.")

    # Process each row
    for index, row in df.iterrows():
        print(f"Processing News row {index}")
        text = row[content_column]  # Get the text content
        if pd.notna(text):  # Check if the text is not null
            output_file = os.path.join(output_dir, f"news_row_{index}_text.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
    print("News text extraction completed.")

# Main function to run all preprocessing steps
if __name__ == "__main__":
    # Input directories/files
    pdf_dir = "../data/pdfs"
    wikileaks_file = "../data/wikileaks_parsed.xlsx"
    news_file = "../data/news_excerpts_parsed.xlsx"

    # Output directories
    pdf_text_dir = "../processed_data/pdf_texts"
    wikileaks_text_dir = "../processed_data/wikileaks_texts"
    news_text_dir = "../processed_data/news_texts"

    # Process each source
    extract_text_from_pdfs(pdf_dir, pdf_text_dir)
    extract_text_from_wikileaks_grouped(wikileaks_file, wikileaks_text_dir)
    extract_text_from_news(news_file, news_text_dir)
