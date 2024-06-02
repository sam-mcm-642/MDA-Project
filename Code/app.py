import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import math
import unicodedata
import googlemaps

# Read Mapbox access token
with open("mapbox_token.txt") as f:
    mapbox_access_token = f.read().strip()

# Set Mapbox access token & googlemaps token
px.set_mapbox_access_token(mapbox_access_token)

with open("googlemaps_token.txt") as f:
    googlemaps_token = f.read().strip()
gmaps = googlemaps.Client(key=googlemaps_token)

# Load the CSV files
data_path = "/Users/Jovan/Desktop/MDA-Project/Data/"

df_app = pd.read_csv("/4_DataApp/app_data.csv")
df_cards = pd.read_csv(data_path + "/cards_with_density.csv")
df_coverage = pd.read_csv("/4_DataApp/coverage.csv")

# Replace "Lige" with "Liège" after applying the function
df_app['city'] = df_app['city'].replace("Liege", "Liège")
df_cards['city'] = df_cards['city'].replace("Liege", "Liège")
df_coverage['city'] = df_coverage['city'].replace("Liege", "Liège")


app = dash.Dash(__name__)
server = app.server

city_options = [
    {"label": "Antwerpen", "value": "Antwerpen"},
    {"label": "Brugge", "value": "Brugge"},
    {"label": "Brussels", "value": "Brussels"},
    {"label": "Charleroi", "value": "Charleroi"},
    {"label": "Gent", "value": "Gent"},
    {"label": "Leuven", "value": "Leuven"},
    {"label": "Liège", "value": "Liège"},
    {"label": "Oostende", "value": "Oostende"}
]

visualization_options = [
    {"label": "Scatter Plot", "value": "scatter"},
    {"label": "Heatmap", "value": "heatmap"},
    {"label": "Buffer Zones", "value": "buffer_zones"}
]

label_map = {'old_aed': 'Old AED', 'card': 'Cardiac arrest', 'new_aed': 'New AED'}
df_app['type'] = df_app['type'].map(label_map)

app.layout = html.Div([
    html.H1("MDA Project dashboard", style={'background-color': 'lightblue', 'padding': '10px'}),
    html.H2("Made by Sam McManagan, Jovan Samardžić, Lucas Coolsaet, Kristian Hussar"),
    html.Div([
        dcc.Dropdown(
            id='city-dropdown',
            options=city_options,
            value='Antwerpen',
            clearable=False
        ),
    ], style={'padding': '10px'}),

    html.Div([
        html.Div([
            dcc.Graph(id='map-graph', style={'width': '80vw', 'height': 'calc(100vh - 150px)', 'display': 'inline-block'})
        ], style={'display': 'inline-block', 'vertical-align': 'top'}),
        
        html.Div([
            dcc.Checklist(
                id='visualization-selector',
                options=visualization_options,
                value=['scatter'],  
                inputStyle={"margin-right": "10px", "display": "block"}
            ),
            html.Div(id='legend-div'),

            # Div for the coverage text, placed after the selection options
            html.Div([
                html.Div([
                    html.P(id='coverage-header', style={'margin-bottom': '5px', 'font-weight': 'bold'}),
                    html.P(id='old-coverage', style={'margin-bottom': '5px'}),
                    html.P(id='new-coverage', style={'margin-bottom': '5px'})
                ], style={'padding': '10px', 'float': 'right', 'width': '100%', 'clear': 'right'}),
            ])
        ], style={'width': '15vw', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '10px', 'background-color': 'white'}),
        
    ]),

    # Slider div
    html.Div([
        dcc.Slider(
            id='buffer-radius-slider',
            min=100,
            max=400,
            step=50,
            value=300,
            marks={i: f'{i}m' for i in range(100, 400, 50)},
            tooltip={"placement": "bottom", "always_visible": True}
        ),
    ], style={'padding': '10px'}),
    
])




# Define callback to update the map and coverage based on the selected city, visualization, and buffer radius
@app.callback(
    [Output('map-graph', 'figure'), Output('coverage-header', 'children'), Output('old-coverage', 'children'), Output('new-coverage', 'children')],
    [Input('city-dropdown', 'value'), Input('visualization-selector', 'value'), Input('buffer-radius-slider', 'value'), Input('map-graph', 'clickData')]
)
def update_map(selected_city, selected_visualizations, buffer_radius, clickData):
    # Filter the DataFrame for the selected city
    filtered_df = df_app[df_app['city'] == selected_city]
    filtered_cards = df_cards[df_cards['city'] == selected_city]

    fig = go.Figure()
    # Create a figure object for the map
    fig = px.scatter_mapbox(
        filtered_df,
        lat="lat",
        lon="lon",
        color="type",
        color_discrete_map={"Old AED": "black", "Cardiac arrest": "red", "New AED": "cyan"},
        size_max=15,
        zoom=12
    )

        # Add buffer zones if selected
    if "buffer_zones" in selected_visualizations:
        

        # Iterate over AED locations and add buffer zones as filled circles
        for _, row in filtered_df[filtered_df['type'] == 'Old AED'].iterrows():
            circle_lats, circle_lons = calculate_circle_coordinates(row['lat'], row['lon'], buffer_radius)
            fig.add_trace(
                go.Scattermapbox(
                    mode="markers",
                    lon=circle_lons,
                    lat=circle_lats,
                    fill="toself",
                    fillcolor='rgba(0, 0, 255, 0.2)',
                    marker=dict(
                        size=2,
                        color='rgba(0, 0, 255, 0.2)',
                        symbol='circle',  # Symbol type for the scatter plot
                        opacity=0.2,  # Set opacity for the circles
                        
                    ),
                    showlegend=False
                )
            )

    if "heatmap" in selected_visualizations:
        fig.add_trace(
            go.Densitymapbox(
                lat=filtered_cards['lat'],
                lon=filtered_cards['lon'],
                z=filtered_cards['density'],
                radius=16,
                colorscale='Viridis',
                showscale=False
            )
        )
        fig.update_layout(
            mapbox=dict(
                center=dict(lat=filtered_cards['lat'].mean(), lon=filtered_cards['lon'].mean()),
                zoom=12
            )
        )

    fig.update_layout(
        mapbox_style="streets",
        title=f"AEDs and Cards in {selected_city}",
        margin=dict(l=0, r=0, t=0, b=0)
    )

    # Get coverage data for the selected city
    selected_coverage = df_coverage[df_coverage['city'] == selected_city]
    old_coverage = selected_coverage['old_coverage'].iloc[0]
    new_coverage = selected_coverage['new_coverage'].iloc[0]
    # Round the coverage values to 2 decimal places
    old_coverage_rounded = round(old_coverage, 2)
    new_coverage_rounded = round(new_coverage, 2)
    coverage_text = [
            f"Coverage in {selected_city}:",
            f"Old Coverage: {old_coverage_rounded}%",
            f"New Coverage: {new_coverage_rounded}%"
        ]

    # Check if a point was clicked
    if clickData:
        clicked_lat = clickData['points'][0]['lat']
        clicked_lon = clickData['points'][0]['lon']
        
        # Find the closest AED for the clicked cardiac arrest point
        closest_aed = df_app[(df_app['lat'] == clicked_lat) & (df_app['lon'] == clicked_lon)].iloc[0]
        aed_lat = closest_aed['aed_lat']
        aed_lon = closest_aed['aed_lon']
        distance = closest_aed['distance']

        # Fetch the walking route from the cardiac arrest point to the closest AED using Google Maps Directions API
        directions_result = gmaps.directions(
            (clicked_lat, clicked_lon),
            (aed_lat, aed_lon),
            mode="walking"
        )

        # Extract the polyline points from the directions result
        if directions_result:
            polyline_points = directions_result[0]['overview_polyline']['points']
            decoded_polyline = googlemaps.convert.decode_polyline(polyline_points)

            # Extract latitudes and longitudes from the decoded polyline
            route_lats = [point['lat'] for point in decoded_polyline]
            route_lons = [point['lng'] for point in decoded_polyline]

            # Add the polyline route to the map
            fig.add_trace(
                go.Scattermapbox(
                    mode="lines",
                    lon=route_lons,
                    lat=route_lats,
                    line=dict(width=2, color='blue'),
                    name='Route to AED',
                    hovertext=f"Distance: {distance} meters"
                )
            )

    return fig, coverage_text[0], coverage_text[1], coverage_text[2]

# Function to calculate circle coordinates
def calculate_circle_coordinates(lat, lon, radius):
    radius_degrees = radius / 111000  # Convert radius to degrees (approximation)
    circle_lats = []
    circle_lons = []
    for angle in range(0, 360, 5):
        angle_rad = math.radians(angle)
        circle_lat = lat + radius_degrees * math.cos(angle_rad)
        circle_lon = lon + radius_degrees * math.sin(angle_rad) / math.cos(math.radians(lat))
        circle_lats.append(circle_lat)
        circle_lons.append(circle_lon)
    return circle_lats, circle_lons

if __name__ == '__main__':
    app.run_server(debug=True)