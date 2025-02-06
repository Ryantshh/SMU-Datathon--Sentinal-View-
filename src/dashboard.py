import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from wordcloud import WordCloud
import io
import base64

# Load the cleaned relationships JSON file
file_path = '../processed_data/cleaned_extracted_relationships.json'
with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# -----------------------------------------------
# Prepare Data for Threat Level Distribution (Bar Chart)
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
impact_levels = []
threat_types = []
for entry in data:
    impact = entry.get("Threat Assessment", {}).get("Impact level on Singapore", 0)
    ttype = entry.get("Threat Assessment", {}).get("Type", "Unknown")
    loc1 = entry.get("Origin Location 1")
    loc2 = entry.get("Origin Location 2")
    if loc1:
        locations.append(loc1)
        impact_levels.append(impact)
        threat_types.append(ttype)
    if loc2 and loc1 != loc2:
        locations.append(loc2)
        impact_levels.append(impact)
        threat_types.append(ttype)
df_geo = pd.DataFrame({'Location': locations, 'Impact Level': impact_levels, 'Threat Type': threat_types})
df_geo = df_geo.dropna()
df_geo = df_geo[df_geo['Impact Level'] > 0]

# -----------------------------------------------
# Prepare Data for Heatmap Visualization (Old Heatmap for Threat Levels 5-10)
entity_1_list_heat = []
entity_2_list_heat = []
threat_level_list_heat = []
for record in data:
    tlevel = record['Threat Assessment'].get('Threat Level', 0)
    # Only include threat levels 5 to 10 for the heatmap
    if 5 <= tlevel <= 10:
        ent1 = record.get('Entity 1', '').strip()
        ent2 = record.get('Entity 2', '').strip()
        if ent1 and ent2:
            entity_1_list_heat.append(ent1)
            entity_2_list_heat.append(ent2)
            threat_level_list_heat.append(tlevel)
df_heatmap = pd.DataFrame({
    'Entity 1': entity_1_list_heat,
    'Entity 2': entity_2_list_heat,
    'Threat Level': threat_level_list_heat
})
# Pivot the data: if duplicate (Entity 1, Entity 2) pairs exist, take the max threat level
heatmap_data = df_heatmap.pivot_table(
    index='Entity 1',
    columns='Entity 2',
    values='Threat Level',
    aggfunc='max'
).fillna(0)
# Remove rows and columns that are entirely zeros
heatmap_data = heatmap_data.loc[(heatmap_data != 0).any(axis=1), (heatmap_data != 0).any(axis=0)]
# Create the old heatmap using px.imshow; fixing the color scale to 5-10 so that nonzero values stand out
old_heatmap_fig = px.imshow(
    heatmap_data,
    labels={'x': 'Entity 2', 'y': 'Entity 1', 'color': 'Threat Level'},
    title='Entity Pair Frequency and Threat Level Heatmap (Levels 5-10)',
    color_continuous_scale='Oranges',
    template="plotly_dark",
    zmin=5,
    zmax=10
)
old_heatmap_fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    height=800,
    xaxis=dict(tickangle=-45)
)

# -----------------------------------------------
# Bar Chart Data Preparation (Impact Levels)
df_bar = df_geo.groupby(['Threat Type', 'Impact Level'], as_index=False).size()
def create_bar_chart(threat_level_filter):
    filtered_df = df_bar[df_bar['Impact Level'] >= threat_level_filter]
    filtered_df = filtered_df.sort_values(by='Impact Level', ascending=False)
    fig = px.bar(
        filtered_df,
        x="Threat Type",
        y="Impact Level",
        color="Threat Type",
        title="Impact Level on Singapore by Threat Type",
        template="plotly_dark"
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig

# -----------------------------------------------
# Prepare Data for Treemap (Entity Threat Levels by Threat Type)
entity_list_treemap = []
threat_level_list_treemap = []
threat_type_list_treemap = []
for record in data:
    entity_list_treemap.append(record['Entity 1'])
    threat_level_list_treemap.append(record['Threat Assessment']['Threat Level'])
    threat_type_list_treemap.append(record['Threat Assessment'].get('Type'))
    entity_list_treemap.append(record['Entity 2'])
    threat_level_list_treemap.append(record['Threat Assessment']['Threat Level'])
    threat_type_list_treemap.append(record['Threat Assessment'].get('Type'))
df_treemap = pd.DataFrame({
    'Entity': entity_list_treemap,
    'Threat Level': threat_level_list_treemap,
    'Threat Type': threat_type_list_treemap
})
# Replace missing threat types with "Unknown" and filter out zero-threat entries
df_treemap['Threat Type'] = df_treemap['Threat Type'].fillna("Unknown")
df_treemap = df_treemap[df_treemap['Threat Level'] > 0]
treemap_fig = px.treemap(
    df_treemap,
    path=['Threat Type', 'Entity'],
    values='Threat Level',
    color='Threat Level',
    color_continuous_scale='Oranges',
    template="plotly_dark",
    title="Treemap of Entity Threat Levels by Threat Type"
)
treemap_fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)

# -----------------------------------------------
# Prepare Data for Word Cloud (for Selected Entity Pair)
entity_list_wc = []
entity_2_list_wc = []
relationship_summary_list = []
relevant_context_list = []
for record in data:
    entity_list_wc.append(record['Entity 1'])
    entity_2_list_wc.append(record['Entity 2'])
    relationship_summary_list.append(record['Relationship Summary'])
    relevant_context_list.append(record['Relevant Context'])
df_wordcloud = pd.DataFrame({
    'Entity 1': entity_list_wc,
    'Entity 2': entity_2_list_wc,
    'Relationship Summary': relationship_summary_list,
    'Relevant Context': relevant_context_list
})
valid_pairs = df_wordcloud[
    (df_wordcloud['Relationship Summary'].str.strip() != '') |
    (df_wordcloud['Relevant Context'].str.strip() != '')
]
entity_pairs = valid_pairs[['Entity 1', 'Entity 2']].drop_duplicates()
dropdown_options = [
    {'label': f'{e1} & {e2}', 'value': f'{e1} & {e2}'}
    for e1, e2 in zip(entity_pairs['Entity 1'], entity_pairs['Entity 2'])
]

# -----------------------------------------------
# Dash App Layout and Callbacks using Darkly Theme
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand=html.Span("Sentinel View", style={
            'fontSize': '2.5rem',
            'fontFamily': "'Montserrat', sans-serif",
            'fontWeight': 'bold'
        }),
        brand_href="#",
        color="dark",
        dark=True,
        fluid=True,
        className="mb-4"
    ),
    dbc.Row([
        dbc.Col([
            html.H2("Entity Relationship Graph"),
            html.Iframe(src='/assets/entity_relationship_graph.html', width='100%', height='600px', style={'border': 'none'})
        ], width=12)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            html.H2("Threat Level and Collaborations Distribution Across Entities"),
            dcc.Graph(id='threat-level-bar', config={'displayModeBar': False}),
            dcc.Slider(
                id='threat-slider',
                min=df['Threat Level'].min(),
                max=df['Threat Level'].max(),
                value=df['Threat Level'].min(),
                marks={i: str(i) for i in range(df['Threat Level'].min(), df['Threat Level'].max() + 1)},
                step=1
            )
        ], width=12)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
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
                    color_continuous_scale="Reds",
                    template="plotly_dark"
                ).update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"),
                style={'height': '600px', 'width': '100%'}
            )
        ], width=12)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            html.H2("Impact Levels to Singapore"),
            dcc.Graph(id='bar-chart', figure=create_bar_chart(0), style={'height': '600px', 'width': '100%'}),
            dcc.Slider(
                id='impact-level-slider',
                min=df_bar['Impact Level'].min(),
                max=df_bar['Impact Level'].max(),
                value=df_bar['Impact Level'].min(),
                marks={int(i): str(i) for i in range(int(df_bar['Impact Level'].min()), int(df_bar['Impact Level'].max()) + 1)},
                step=1
            )
        ], width=12)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            html.H2("Threat Level Heatmap"),
            dcc.Graph(
                id='heatmap',
                figure=old_heatmap_fig,
                style={'height': '800px', 'width': '100%'}
            )
        ], width=12)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            html.H2("Treemap of Entity Threat Levels by Threat Type"),
            dcc.Graph(
                id='treemap',
                figure=treemap_fig,
                style={'height': '800px', 'width': '100%'}
            )
        ], width=12)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            html.H2("Word Cloud for Selected Entities"),
            html.Div([
                dbc.Label("Select Entity Pair:"),
                dcc.Dropdown(
                    id='entity-dropdown',
                    options=dropdown_options,
                    value=dropdown_options[0]['value'],
                    multi=False,
                    clearable=False,
                    style={'color': 'black'}
                )
            ], className="mb-3"),
            html.Div(id='wordcloud-output', children=[])
        ], width=12)
    ])
], fluid=True, style={'backgroundColor': '#121212', 'color': 'white', 'padding': '20px'})

# -----------------------------------------------
# Callbacks
@app.callback(
    Output('threat-level-bar', 'figure'),
    Input('threat-slider', 'value')
)
def update_threat_level_chart(threat_level):
    filtered_df = grouped_df[grouped_df['Threat Level'] == threat_level]
    fig = px.bar(
        filtered_df,
        x='Entity',
        y='Collaboration Count',
        color='Threat Level',
        title='Threat Level and Collaborations Distribution across Entities',
        labels={'Collaboration Count': 'Number of Collaborations', 'Entity': 'Entity'},
        template="plotly_dark"
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig

@app.callback(
    Output('wordcloud-output', 'children'),
    Input('entity-dropdown', 'value')
)
def update_wordcloud(selected_pair):
    entity_1, entity_2 = selected_pair.split(' & ')
    filtered_data = df_wordcloud[(df_wordcloud['Entity 1'] == entity_1) & (df_wordcloud['Entity 2'] == entity_2)]
    text = " ".join(filtered_data['Relationship Summary'].tolist() + filtered_data['Relevant Context'].tolist())
    if not text.strip():
        return html.Div("No relevant text available for the selected entity pair.", style={'color': 'white'})
    wordcloud = WordCloud(width=800, height=400, background_color='black', colormap='viridis').generate(text)
    img = io.BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    img_b64 = base64.b64encode(img.getvalue()).decode('utf-8')
    return html.Img(src=f'data:image/png;base64,{img_b64}', style={'width': '80%', 'height': '80%'})

@app.callback(
    Output('bar-chart', 'figure'),
    Input('impact-level-slider', 'value')
)
def update_bar_chart(threat_level):
    return create_bar_chart(threat_level)

if __name__ == '__main__':
    app.run_server(debug=True)
