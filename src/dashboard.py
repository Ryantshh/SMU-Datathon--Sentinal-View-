import json
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
from wordcloud import WordCloud
import io
import base64

# Load the cleaned relationships JSON file
file_path = '../processed_data/cleaned_extracted_relationships.json'
with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# -----------------------------------------------
# Prepare Data for Threat Level Distribution
entity_list = []
threat_level_list = []

for record in data:
    entity_list.append(record['Entity 1'])
    threat_level_list.append(record['Threat Assessment']['Threat Level'])
    entity_list.append(record['Entity 2'])
    threat_level_list.append(record['Threat Assessment']['Threat Level'])

df = pd.DataFrame({'Entity': entity_list, 'Threat Level': threat_level_list})
grouped_df = df.groupby(['Entity', 'Threat Level']).size().reset_index(name='Collaboration Count')

# -----------------------------------------------
# Prepare Data for Threat Origins Geo Map
locations = []
threat_levels = []
threat_types = []

for entry in data:
    threat_level = entry.get("Threat Assessment", {}).get("Impact level on Singapore", 0)
    threat_type = entry.get("Threat Assessment", {}).get("Type", "Unknown")

    location1 = entry.get("Origin Location 1")
    location2 = entry.get("Origin Location 2")

    if location1:
        locations.append(location1)
        threat_levels.append(threat_level)
        threat_types.append(threat_type)

    if location2 and location1 != location2:
        locations.append(location2)
        threat_levels.append(threat_level)
        threat_types.append(threat_type)

df_geo = pd.DataFrame({'Location': locations, 'Impact Level': threat_levels, 'Threat Type': threat_types})
df_geo = df_geo.dropna()
df_geo = df_geo[df_geo['Impact Level'] > 0]

# -----------------------------------------------
# Prepare Data for Heatmap Visualization
entity_1_list = []
entity_2_list = []
threat_level_list = []

for record in data:
    threat_level = record['Threat Assessment'].get('Threat Level', 0)

    if threat_level > 5:  # Only include Threat Levels > 5
        entity_1 = record.get('Entity 1', '').strip()
        entity_2 = record.get('Entity 2', '').strip()

        if entity_1 and entity_2:
            entity_1_list.append(entity_1)
            entity_2_list.append(entity_2)
            threat_level_list.append(threat_level)

df_heatmap = pd.DataFrame({'Entity 1': entity_1_list, 'Entity 2': entity_2_list, 'Threat Level': threat_level_list})
heatmap_data = df_heatmap.pivot(index='Entity 1', columns='Entity 2', values='Threat Level').fillna(0)
heatmap_data = heatmap_data.loc[(heatmap_data != 0).any(axis=1), (heatmap_data != 0).any(axis=0)]

# -----------------------------------------------
# Bar Chart Data Preparation
df_bar = df_geo.groupby(['Threat Type', 'Impact Level'], as_index=False).size()

def create_bar_chart(threat_level_filter):
    filtered_df = df_bar[df_bar['Impact Level'] >= threat_level_filter]
    filtered_df = filtered_df.sort_values(by='Impact Level', ascending=False)

    fig = px.bar(
        filtered_df,
        x="Threat Type",
        y="Impact Level",
        color="Threat Type",
        title="Impact Level on Singapore by Threat Type"
    )
    return fig

# -----------------------------------------------
# Prepare Data for Entity Pair and Word Cloud
entity_1_list = []
entity_2_list = []
relationship_summary_list = []
relevant_context_list = []

for record in data:
    entity_1_list.append(record['Entity 1'])
    entity_2_list.append(record['Entity 2'])
    relationship_summary_list.append(record['Relationship Summary'])
    relevant_context_list.append(record['Relevant Context'])

df_wordcloud = pd.DataFrame({
    'Entity 1': entity_1_list,
    'Entity 2': entity_2_list,
    'Relationship Summary': relationship_summary_list,
    'Relevant Context': relevant_context_list
})

# Filter entity pairs with non-empty Relationship Summary or Relevant Context
valid_pairs = df_wordcloud[(df_wordcloud['Relationship Summary'].str.strip() != '') | (df_wordcloud['Relevant Context'].str.strip() != '')]
entity_pairs = valid_pairs[['Entity 1', 'Entity 2']].drop_duplicates()

dropdown_options = [
    {'label': f'{entity_1} & {entity_2}', 'value': f'{entity_1} & {entity_2}'}
    for entity_1, entity_2 in zip(entity_pairs['Entity 1'], entity_pairs['Entity 2'])
]

# -----------------------------------------------
# Dash App Layout and Callbacks
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Entity Analysis Dashboard"),

    # Relationship Graph Embed
    html.Div([
        html.H2("Entity Relationship Graph"),
        html.Iframe(src='/assets/entity_relationship_graph.html', width='100%', height='800px')
    ]),

    # Threat Level Distribution with Slider
    html.Div([
        html.H2("Threat Level Distribution Across Entities"),
        dcc.Graph(id='threat-level-bar'),
        dcc.Slider(
            id='threat-slider',
            min=df['Threat Level'].min(),
            max=df['Threat Level'].max(),
            value=df['Threat Level'].min(),
            marks={i: str(i) for i in range(df['Threat Level'].min(), df['Threat Level'].max() + 1)},
            step=1
        )
    ]),

    # Threat Origins Geo Map
    html.Div([
        html.H2("Threat Origins and Impact Levels to Singapore"),
        dcc.Graph(
            id='geo-map',
            figure=px.scatter_geo(
                df_geo,
                locations="Location",
                locationmode="country names",
                size="Impact Level",
                color="Impact Level",
                hover_name="Location",
                title="Threat Origins and Impact Levels to Singapore",
                projection="natural earth",
                color_continuous_scale="Reds"
            ),
            style={'height': '900px', 'width': '100%'}
        ),
    ]),

    # Bar Chart for Impact Levels
    html.Div([
        html.H2("Impact Levels to Singapore"),
        dcc.Graph(id='bar-chart', figure=create_bar_chart(0), style={'height': '900px', 'width': '100%'}),
        dcc.Slider(
            id='impact-level-slider',
            min=df_bar['Impact Level'].min(),
            max=df_bar['Impact Level'].max(),
            value=df_bar['Impact Level'].min(),
            marks={int(i): str(i) for i in range(int(df_bar['Impact Level'].min()), int(df_bar['Impact Level'].max()) + 1)},
            step=1
        ),
    ]),

    # Heatmap Visualization
    html.Div([
        html.H2("Threat Level Heatmap"),
        dcc.Graph(
            id='heatmap',
            figure=px.imshow(
                heatmap_data,
                labels={'x': 'Entity 2', 'y': 'Entity 1', 'color': 'Threat Level'},
                title='Entity Pair Frequency and Threat Level Heatmap',
                color_continuous_scale='Oranges'
            ),
            style={'height': '1000px', 'width': '100%'}
        ),
    ]),

    # Word Cloud for Entity Pair
    html.Div([
        html.H2("Word Cloud for Selected Entities"),
        html.Div([
            html.Label("Select Entity Pair:"),
            dcc.Dropdown(
                id='entity-dropdown',
                options=dropdown_options,
                value=dropdown_options[0]['value'],
                multi=False
            )
        ]),
        html.Div(id='wordcloud-output', children=[])
    ])
])

# Callback to dynamically update threat-level bar chart
@app.callback(
    Output('threat-level-bar', 'figure'),
    Input('threat-slider', 'value')
)
def update_threat_level_chart(threat_level):
    filtered_df = grouped_df[grouped_df['Threat Level'] == threat_level]
    return px.bar(
        filtered_df,
        x='Entity',
        y='Collaboration Count',
        color='Threat Level',
        title='Threat Level Distribution across Entities',
        labels={'Collaboration Count': 'Number of Collaborations', 'Entity': 'Entity'},
        color_continuous_scale='Viridis'
    )

# Callback for Word Cloud update
@app.callback(
    Output('wordcloud-output', 'children'),
    Input('entity-dropdown', 'value')
)
def update_wordcloud(selected_pair):
    entity_1, entity_2 = selected_pair.split(' & ')
    filtered_data = df_wordcloud[(df_wordcloud['Entity 1'] == entity_1) & (df_wordcloud['Entity 2'] == entity_2)]

    text = " ".join(filtered_data['Relationship Summary'].tolist() + filtered_data['Relevant Context'].tolist())
    if not text.strip():
        return html.Div("No relevant text available for the selected entity pair.")

    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    img = io.BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)

    img_b64 = base64.b64encode(img.getvalue()).decode('utf-8')
    return html.Img(src=f'data:image/png;base64,{img_b64}', style={'width': '80%', 'height': '80%'})

# Callback for dynamic bar chart update
@app.callback(
    Output('bar-chart', 'figure'),
    [Input('impact-level-slider', 'value')]
)
def update_bar_chart(threat_level):
    return create_bar_chart(threat_level)

if __name__ == '__main__':
    app.run_server(debug=True)
