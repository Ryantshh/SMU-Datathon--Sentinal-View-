
# Entity Analysis Dashboard

This project is an interactive Dashboard that visualizes threat levels and their associated data for various entities. The dashboard is powered by Dash and Plotly to provide real-time visualizations such as bar charts, heatmaps, word clouds, and geospatial maps.

The dashboard uses data on threat assessments, entity relationships, and other related information, allowing users to explore various aspects of the threat landscape.

## Project Structure 
Project Directory
├── data                         # Contains source data files in various formats
│   ├── pdfs                     # Folder for raw PDF files used for analysis
│   ├── news_excerpts_parsed.xlsx # Excel file with parsed news excerpts
│   └── wikileaks_parsed.xlsx    # Parsed data extracted from Wikileaks
├── processed_data               # Contains preprocessed and extracted data files
│   ├── news_texts               # Folder for parsed news article text data
│   ├── pdf_texts                # Folder for parsed text extracted from PDFs
│   ├── wikileaks_texts          # Folder for text extracted from Wikileaks documents
│   ├── cleaned_extracted_relationships.json # Cleaned relationships between entities
│   ├── cleaned_filtered_entities.json       # Filtered entity data
│   ├── combined_entities.json   # Combined entity data from multiple sources
│   ├── extracted_relationships.json # Raw extracted relationships
│   └── standardized_final_extracted_relationships.json # Final standardized relationships data
├── src                          # Source code for data processing and dashboard
│   ├── assets                   # Static assets for the dashboard
│   │   ├── entity_relationship_graph.html # HTML file for the entity relationship graph visualization
│   │   └── graph_data.js        # JavaScript file for graph data handling
│   ├── nodeGenerator.py         # Script for generating graph nodes for visualization
│   ├── lib                      # Python library for data extraction and preprocessing
│   │   ├── api.py               # API integration for data extraction
│   │   ├── clean_entities.py    # Script for cleaning extracted entity data
│   │   ├── dashboard.py         # Dashboard application script
│   │   ├── extract_entities.py  # Script for extracting entities from text data
│   │   ├── extract_relationships_API.py  # Script for extracting relationships via API
│   │   ├── extract_relationships_Local.py # Script for local relationship extraction
│   │   ├── preprocess.py        # Data preprocessing utilities
│   │   └── standardize_json.py  # Script for standardizing JSON data

## Dependencies

This project requires the following Python packages:

- dash: pip install dash
- pandas: pip install pandas
- plotly: pip install plotly
- wordcloud: pip install wordcloud
- geopandas (for geospatial visualizations): pip install geopandas
- numpy: pip install numpy (if needed for array manipulation)

## Setup (THE RAW DATA HAS TO BE IN A FOLDER CALLED DATA)

1. Run "src/preprocess.py" which will generate the "processed_data/news_texts" folder, "pdf_texts" folder and the "processed_data/wikileaks_texts" folder.
2. Run the "src/extract_entities.py" and the "src/clean_entities.py" to extract the entities. This would create the "processed_data/combined_entities.json and the "processed_data/cleaned_filtered_entities.json".
3. Run the "src/extract_relationships_API.py" and the "src/standardize_json.py to extract the relationships between entities and to standardise the output.
4. Run the src/assets/nodeGenerator.py which will geneate the src/assets/graph_data.js.
5. Run the src/dashboard.py and a browser would be open to view and analyse the data.
## Features

- Threat Level Distribution: Visualizes the distribution of threat levels across different entities in a bar chart.
- Threat Origins Geo Map: Displays the locations of potential threats and their impact on Singapore on a geographical map.
- Impact Levels Bar Chart: Allows dynamic filtering of threat impact levels, updated through a slider.
- Threat Level Heatmap: Shows the frequency and threat levels between different entity pairs in a heatmap format.
- Word Cloud: Displays a word cloud for the selected entity pair, based on relationship summaries and relevant context.
