import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd

# Create the app
app = dash.Dash(__name__)

# Load dataset using Plotly
tips = px.data.tips()

fig = px.scatter(tips, x="total_bill", y="tip") # Create a scatterplot

app.layout = html.Div(children=[
   html.H1(children='Dash'),  # Create a title with H1 tag

   html.Div(children='''
       Dash: A web application framework for your data.
   '''),  # Display some text

   dcc.Graph(
       id='example-graph',
       figure=fig
   )  # Display the Plotly figure
])

if __name__ == '__main__':
   app.run_server(debug=True) # Run the Dash app