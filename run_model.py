"""
run_model.py
-------------
This script creates the interactive model.
When it is run, Dash should run on a local port and it should just open in the browser.
"""

import folium
import polars as pl
import pandas as pd
from dash import Dash, dcc, html, Input, Output, callback
import plotly.express as px
from threading import Timer
import statsmodels.api as sm 

from modules.dash_visualisation import open_browser

file_path = "data/"
map_path = "maps/"

# Accessible colour scheme
ONS_COLOURS = {
    "Dark blue":    "#12436D",
    "Turquoise":    "#28A197",
    "Dark pink":    "#801650",
    "Orange": 	    "#F46A25",	
    "Dark grey":    "#3D3D3D",
    "Light purple": "#A285D1",
}

# 1) Where London’s BikePoints are currently
# 1a) Visual map
full_demographics_data = pl.read_csv(file_path + "model_data.csv")
bikepoints = pl.read_csv(file_path + "bikepoints.csv")
list_of_locations = list(zip(list(bikepoints["lat"]), list(bikepoints["lon"])))

center_of_london = [51.5074, -0.1272]
map_1 = folium.Map(location=center_of_london, zoom_start= 12)
for point in list_of_locations:
    folium.CircleMarker(point, radius = 2).add_to(map_1)
map_1.save(map_path + "map_1.html")

# Logistic Regression - Won't be printed but useful to know
log_reg_data = full_demographics_data.drop(["bikepoint", "la_name"]).drop_nulls()
X = log_reg_data.drop("bikepoint_binary")
y = log_reg_data["bikepoint_binary"]
# log_reg = sm.Logit(y.to_pandas(), X.to_pandas()).fit()
"""
Regression Findings
--------------------
# Obesity decreased post-BikePoint introduction
# Overweight-ness increased by less post-BikePoint introduction
# Neither childhood obesity nor overweightness correlate with BikePoint placement at Reception level
# Neither childhood obesity nor overweightness correlate with BikePoint placement at Y6 level
# Adults are less overweight in areas with BikePoints
# Deprivation is higher in areas with BikePoints
# Otherwise, deprivation usually correlates positively with obesity / overweight
"""
# 2) Where might benefit from new BikePoints from a public health perspective
# Mean journey = 17 mins
# Network effects mean they have to be proximal
# i) Nearby, best choice, biasing for deprevation / obesity (SE)
map_2 = map_1
old_kent_road = [51.482892245020764, -0.08350725324780937]
okr_quote = """
    <h4> Strongly Recommended: South East </h4>
    New bikepoints would be useful here because they:
    <ol>
    <li>Would easily integrate with existing BikePoints to the North, West and East</li>
    <li>Cover an area of above average deprivation and obesity</li>
    <li>Move towards areas of high obesity and deprivation (SE / E London)</li>
    </ol>
    </p>
    """
folium.CircleMarker(old_kent_road, radius = 40, color = "green", popup = folium.Popup(okr_quote, min_width = 300, max_width = 300)).add_to(map_2)

# ii) Nearby, second best, high deprivation, not as good network (E)
canning_town = [51.52536687233129, -0.009067582695335391]
ct_quote = """
    <h4> Consider: East </h4>
    New bikepoints would be useful here because they:
    <ol>
    <li>Would easily integrate with existing BikePoints to the West</li>
    <li>Cover an area of above average deprivation and obesity</li>
    <li>Move towards areas of higher deprivation (E London)</li>
    </ol>
    </p>
    """
folium.CircleMarker(canning_town, radius = 40, color = "yellow", popup = folium.Popup(ct_quote, min_width = 300, max_width = 300)).add_to(map_2)

# iii) Nearby, towards some deprivation, worse network (N)
islington = [51.53865911744296, -0.10777669328734478]
is_quote = """
    <h4> Consider: North </h4>
    New bikepoints would be useful here because they:
    <ol>
    <li>Would easily integrate with existing bikepoints to the South</li>
    <li>Cover an area of above average deprivation and obesity</li>
    <li>Move towards areas of moderate obesity (N London)</li>
    </ol>
    </p>
    """
folium.CircleMarker(islington, radius = 40, color = "yellow", popup = folium.Popup(is_quote, min_width = 300, max_width = 300)).add_to(map_2)

# iv) Worst choice, towards affluence and crowded richmond park (SW)
richmond = [51.46533077682026, -0.243703010739770381]
rich_quote = """
    <h4> Not Recommended: South West </h4>
    New BikePoints would not likely bring much benefit here as:
    <ol>
    <li>The area is high affluence and low obesity</li>
    <li>There are already heavily congested roads for cyclists due to Richmond park</li>
    <li>It moves towards areas of lower obesity (Affluent W/ SW London)</li>
    </ol>
    </p>
    """
folium.CircleMarker(richmond, radius = 70, color = "red", popup = folium.Popup(rich_quote, min_width = 300, max_width = 300)).add_to(map_2)

# v) Worst choice, towards afluence and Kew / chiswick (SW)
chiswick = [51.49289581291107, -0.25124804822200003]
chis_quote = """
    <h4> Not Recommended: West </h4>
    New BikePoints would not likely bring much benefit here as:
    <ol>
    <li>The area is high affluence and low obesity</li>
    <li>It moves towards areas of lower obesity (Affluent W/ SW London)</li>
    </ol>
    </p>
    """
folium.CircleMarker(chiswick, radius = 70, color = "red", popup = folium.Popup(chis_quote, min_width = 300, max_width = 300)).add_to(map_2)
map_2.save(map_path + "map_2.html")

# 3) Any other insights from the data you think are relevant or will capture the interest of the decision maker
# How deprivation relates to BikePoints
deprivation_plot = px.bar(
            log_reg_data.group_by(pl.col("bikepoint_binary")).mean(), 
            x= "bikepoint_binary",
            y = "rank",
            color = "bikepoint_binary",
            color_discrete_map = {True : ONS_COLOURS["Dark blue"], False: ONS_COLOURS["Orange"]},
            hover_data = ["rank"]
            )
deprivation_plot.update_xaxes(categoryorder='array', categoryarray= [True, False])
deprivation_plot.update_layout(
        showlegend=False,
        title= f"How Deprivation relates to BikePoint presence in London",
        xaxis_title="Does the local authority have a BikePoint?",
        yaxis_title= f"Deprivation Rank (1 = Most Deprived)",
        yaxis_range= [0, 20000]
        )

# Now the model can actually begin!
app = Dash(__name__)

graph_df = log_reg_data

#TODO: There must be a neater way of doing paragraphs than this.
app.layout = html.Div([
    html.Div(
        className="app-header",
        children=[
            html.Div('BikePoint Data Review', className="app-header--title")
        ]
   ),
    html.Div(
        children=html.Div([
            html.H2('Introduction'),

            html.Div([
                html.P('This interactive data visualization tool aims to show the reader the following:'),
                html.P('1) The distribution of BikePoint today'),
                html.P('2) The difference between Local Authorities with and without BikePoint (deprivation, adult/teen/childhood obesity)'),
                html.P('3) Potential areas for BikePoint expansion'),
        ]),
        ])
    ),
    html.Div(
        children=html.Div([
            html.H2('Section 1: Distribution of BikePoint across London'),
            html.Div([
                html.P("The interactive map shows the current distribution of BikePoints in blue across central London"),
        ]),
            html.Iframe(id = "map", srcDoc= open(map_path + "map_1.html", "r").read(), height = 500, width = 1000),
        ])
    ),
    html.Div(
        children=html.Div([
            html.H2('Section 2: Local Authority characteristics'),
            html.Div([
                html.P("This bar chart shows the difference between Local Authorities with and without BikePoint."),
                html.P("To chose what is measured on the y-axis, please use to dropdown menu below."),
            ]),
            html.Div([
            dcc.Dropdown(
                options= graph_df.drop(["bikepoint_binary", "rank", "overweight_change", "obese_change"]).columns, 
                id='obesity_bar_graph_control',
                value= graph_df.drop(["bikepoint_binary", "rank"]).columns[0], 
                style={"width": "40%", "padding-left": "5px"}),
            dcc.Graph(figure = {}, id = "obesity_bar_graph", style={'width': '90vh', 'height': '80vh'}),

        ]),
            html.Div([
                html.P("As can be seen above, adult overweight / obesity rates are significantly lower in LAs with BikePoints."),
                html.P("Given that obesity correlates with deprivation, we would expect these areas to be less deprived"),
                html.P("In fact, as can be seen below, local authorities with BikePoints have higher deprivation (they are closer to 1, representing the most deprived LA)"),
        ]),
            html.Div([
                dcc.Graph(figure = deprivation_plot, style={'width': '90vh', 'height': '80vh'}),
                html.P("This may indicate that BikePoints are an effective way of reducing obesity."),
                html.P("Another indicator is that, since 2015, obesity (%) increased less and overweight (%) decreased in areas with BikePoints."),
                html.P("Those without BikePoints saw rises in both metrics."),
                dcc.Dropdown(
                    options= ["overweight_change", "obese_change"], 
                    id='cange_bar_graph_control',
                    value= "overweight_change", 
                    style={"width": "40%", "padding-left": "5px"}),
                dcc.Graph(figure = {}, id = "change_bar_graph", style={'width': '90vh', 'height': '80vh'}),
                html.P("This seems to indicate that BikePoints generate public health improvements in the overweight/obesity domain."),
        ]),
        ])
    ),
        html.Div(
        children=html.Div([
            html.H2('Section 3: Potential areas for BikePoint expansion'),
                html.P("The interactive map shows recommendations for new BikePoint areas"),
                html.P("Please click the circles to read more about why these areas are recommended or recommended against."),
            html.Iframe(id = "map_2", srcDoc= open(map_path + "map_2.html", "r").read(), height = 500, width = 1000),
        ])
    ),
])

@callback(
    Output(component_id="obesity_bar_graph", component_property='figure'),
    Input(component_id='obesity_bar_graph_control', component_property='value'),
)
def update_graph(col_chosen):
    fig = px.bar(
        graph_df.group_by(pl.col("bikepoint_binary")).mean(), 
        x= "bikepoint_binary",
        y = col_chosen,
        color = "bikepoint_binary",
        color_discrete_map = {True : ONS_COLOURS["Dark blue"], False: ONS_COLOURS["Orange"]},
        hover_data= None
    )
    fig.update_xaxes(categoryorder='array', categoryarray= [True, False])
    y_axis_name = (col_chosen.replace('_',' ')).title()
    fig.update_layout(
        showlegend=False,
        title= f"{y_axis_name}(%) vs BikePoint (present/absent)",
        xaxis_title="Does the local authority have a bikepoint?",
        yaxis_title= f"{y_axis_name}(%)",
        yaxis_range= [0, 60],
        )
    return fig

@callback(
    Output(component_id ="change_bar_graph", component_property="figure"),
    Input(component_id='cange_bar_graph_control', component_property='value')
)
def update_graph(col_chosen):
    fig = px.bar(
        graph_df.group_by(pl.col("bikepoint_binary")).mean(), 
        x= "bikepoint_binary",
        y = col_chosen,
        color = "bikepoint_binary",
        color_discrete_map = {True : ONS_COLOURS["Dark blue"], False: ONS_COLOURS["Orange"]},
        hover_data= None
    )
    fig.update_xaxes(categoryorder='array', categoryarray= [True, False])
    y_axis_name = (col_chosen.replace('_',' ')).title()
    fig.update_layout(
        showlegend=False,
        title= f"{y_axis_name}(%) vs BikePoint (present/absent)",
        xaxis_title="Does the local authority have a bikepoint?",
        yaxis_title= f"{y_axis_name}(%)",
        yaxis_range= [-3, +3],
        )
    return fig

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run_server(debug=True, port=1222)