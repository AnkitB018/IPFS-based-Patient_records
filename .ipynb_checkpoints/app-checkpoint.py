import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, MATCH
import json
import os
import ipfshttpclient
from datetime import datetime
from Blockchain import Blockchain
import base64
import re





from login_page import login_layout, login_callbacks
from register_page import register_layout, register_callbacks
from admin_dashboard import layout as admin_layout
from patient_dashboard import layout as patient_layout
from admin_dashboard import register_admin_callbacks
from patient_dashboard import register_patient_callbacks



# File to store user data
USERS_FILE = "users.json"





# Initialize Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Medical Records Login"
server = app.server





# Persistent user store
app.layout = html.Div([
    dcc.Location(id="url", refresh=True),
    dcc.Store(id="session-store", storage_type="session"),
    html.Div(id="page-content")
])




# Routing
@app.callback(Output("page-content", "children"),
              Input("url", "pathname"),
              State("session-store", "data"))
def display_page(pathname, session_data):
    if pathname == "/register":
        return register_layout()
    elif pathname == "/admin":
        if session_data and session_data.get("role") == "admin":
            return admin_layout(session_data["username"])
        else:
            return html.Div("Unauthorized Access", style={"color": "red"})
    elif pathname == "/patient":
        if session_data and session_data.get("role") == "patient":
            return patient_layout(session_data["username"])
        else:
            return html.Div("Unauthorized Access", style={"color": "red"})
    else:
        return login_layout()




# Register page callbacks
register_callbacks(app)

# Login page callbacks
login_callbacks(app)

# Admin callbacks
register_admin_callbacks(app)

# Patient callbacks
register_patient_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)
