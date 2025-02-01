
# Entity Analysis Dashboard

This project is an interactive Dashboard that visualizes threat levels and their associated data for various entities. The dashboard is powered by Dash and Plotly to provide real-time visualizations such as bar charts, heatmaps, word clouds, and geospatial maps.

The dashboard uses data on threat assessments, entity relationships, and other related information, allowing users to explore various aspects of the threat landscape.


## Dependencies

This project requires the following Python packages:

- dash: pip install dash
- pandas: pip install pandas
- plotly: pip install plotly
- wordcloud: pip install wordcloud
- geopandas (for geospatial visualizations): pip install geopandas
- numpy: pip install numpy (if needed for array manipulation)

## Setup

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