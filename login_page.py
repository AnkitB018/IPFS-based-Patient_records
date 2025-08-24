import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import os
import json  

# Path to the users file
USERS_FILE = "users.json"

def load_users():
    USERS_FILE = "users.json"
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}

    # If already in dict form, just return
    if isinstance(data, dict):
        return data

    # If it's a list, convert to dict
    if isinstance(data, list):
        return {u["username"]: u for u in data if "username" in u}

    return {}





def login_layout():
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H2("🔐 Login", className="text-center mb-4"),

                                # Username input
                                dbc.Input(
                                    id="login-username",
                                    type="text",
                                    placeholder="Enter username",
                                    className="mb-3"
                                ),

                                # Password input
                                dbc.Input(
                                    id="login-password",
                                    type="password",
                                    placeholder="Enter password",
                                    className="mb-3"
                                ),

                                # Login button
                                dbc.Button(
                                    "Login",
                                    id="login-button",
                                    color="primary",
                                    className="w-100 mb-2"
                                ),

                                # Login message
                                html.Div(
                                    id="login-message",
                                    className="text-danger text-center mb-3"
                                ),

                                # Go to register
                                dbc.Button(
                                    "Go to Register",
                                    id="to-register",
                                    color="secondary",
                                    outline=True,
                                    className="w-100"
                                ),
                            ]
                        ),
                        className="shadow-sm"
                    ),
                    width=12, md=6, lg=4
                ),
                className="justify-content-center mt-5"
            )
        ],
        fluid=True
    )







def login_callbacks(app):
    @app.callback(
        Output("session-store", "data"),
        Output("url", "pathname", allow_duplicate=True),
        Output("login-message", "children"),
        Input("login-button", "n_clicks"),
        State("login-username", "value"),
        State("login-password", "value"),
        prevent_initial_call=True
    )
    def process_login(n_clicks, username, password):
        users = load_users()

        if not username or not password:
            return dash.no_update, dash.no_update, "Please enter both username and password."

        # Ensure keys exist in loaded user
        if username in users:
            stored_pass = users[username].get("password")
            if stored_pass == password:
                role = users[username].get("role", "patient")
                if role == "admin":
                    return {"username": username, "role": role}, "/admin", ""
                else:
                    return {"username": username, "role": role}, "/patient", ""

        return dash.no_update, dash.no_update, "Invalid username or password."

    @app.callback(
        Output("url", "pathname", allow_duplicate=True),
        Input("to-register", "n_clicks"),
        prevent_initial_call=True
    )
    def go_to_register(n_clicks):
        if n_clicks:
            return "/register"
        return dash.no_update
