import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import json
import os



#helper functions
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


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)
        f.flush()  # ensure data is written immediately
        os.fsync(f.fileno())  # optional, but forces write to disk





# Function for layout
def register_layout():
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H2("📝 Register", className="text-center mb-4"),

                                # Username
                                dbc.Input(
                                    id="reg-username",
                                    type="text",
                                    placeholder="Enter username",
                                    className="mb-3"
                                ),

                                # Patient ID
                                dbc.Input(
                                    id="reg-patient-id",
                                    type="text",
                                    placeholder="Patient ID (only if patient)",
                                    className="mb-3"
                                ),

                                # Password
                                dbc.Input(
                                    id="reg-password",
                                    type="password",
                                    placeholder="Enter password",
                                    className="mb-3"
                                ),

                                # Register button
                                dbc.Button(
                                    "Register",
                                    id="register-button",
                                    color="success",
                                    className="w-100 mb-2"
                                ),

                                # Register message
                                html.Div(
                                    id="register-message",
                                    className="text-danger text-center mb-3"
                                ),

                                # Go to Login
                                dbc.Button(
                                    "Go to Login",
                                    id="to-login",
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




# Function for wrapping callbacks
def register_callbacks(app):
    @app.callback(
        Output("register-message", "children"),
        Output("url", "pathname", allow_duplicate= True),
        Input("register-button", "n_clicks"),
        State("reg-username", "value"),
        State("reg-patient-id", "value"),
        State("reg-password", "value"),
        prevent_initial_call=True
    )
    def process_register(n_clicks, username, patient_id, password):
        users = load_users()
        if not username or not password:
            return "Please enter both username and password.", dash.no_update
        if username in users:
            return "Username already exists.", dash.no_update

        # Determine role
        role = "admin" if username.lower() == "admin" else "patient"
        users[username] = {"password": password, "role": role, "patient_id": patient_id}
        save_users(users)
        return "Registration successful!", "/"



    

    
    @app.callback(
        Output("url", "pathname", allow_duplicate= True),
        Input("to-login", "n_clicks"),
        prevent_initial_call=True
    )
    def go_to_login(n_clicks):
        if n_clicks:
            return "/"
        return dash.no_update
