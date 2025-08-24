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
    """
    Login layout with floating info cards (left & right of login card).
    """

    #  Login Card (center)
    form_card = dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.H2("🔐 Sign in", className="mb-1 fw-bold"),
                        html.Div(
                            "Welcome back — access your blockchain-backed medical records.",
                            className="text-muted mb-3",
                        ),
                    ],
                    style={"textAlign": "left"},
                ),

                dbc.Label("Username", html_for="login-username", className="small fw-semibold"),
                dbc.Input(
                    id="login-username",
                    type="text",
                    placeholder="Enter username",
                    className="mb-3",
                ),

                dbc.Label("Password", html_for="login-password", className="small fw-semibold"),
                dbc.Input(
                    id="login-password",
                    type="password",
                    placeholder="Enter password",
                    className="mb-3",
                ),

                dbc.Button(
                    "Login",
                    id="login-button",
                    color="primary",
                    className="w-100 mb-2",
                    n_clicks=0,
                ),

                html.Div(id="login-message", className="text-danger text-center mb-2"),

                dbc.Button(
                    "Create an account",
                    id="to-register",
                    color="link",
                    className="w-100",
                    style={"textDecoration": "underline"},
                ),
            ]
        ),
        className="shadow-lg border-0 rounded-4 bg-white",
        style={"padding": "20px"},
    )

    #  Left Info Card
    left_info = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Why choose us?", className="fw-bold text-primary mb-3"),
                dbc.ListGroup(
                    [
                        dbc.ListGroupItem("🔐 Secure & immutable records"),
                        dbc.ListGroupItem("🛰️ Decentralized IPFS storage"),
                    ],
                    flush=True,
                    className="small rounded-3 shadow-sm",
                ),
            ]
        ),
        className="shadow border-0 rounded-4 bg-light",
        style={"padding": "15px"},
    )

    #  Right Info Card
    right_info = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Features", className="fw-bold text-primary mb-3"),
                dbc.ListGroup(
                    [
                        dbc.ListGroupItem("🧾 Easy in-browser access"),
                        dbc.ListGroupItem("⚕️ Clinician-ready reports"),
                    ],
                    flush=True,
                    className="small rounded-3 shadow-sm",
                ),
                html.Div(
                    [
                        dbc.Badge("IPFS", color="info", className="me-2"),
                        dbc.Badge("Blockchain", color="success", className="me-2"),
                        dbc.Badge("Patient-first", color="secondary"),
                    ],
                    className="d-flex gap-2 mt-3",
                ),
            ]
        ),
        className="shadow border-0 rounded-4 bg-light",
        style={"padding": "15px"},
        
    )

    #  Outer Container
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.H1("MedRecords", style={"fontWeight": "700", "color": "#0d6efd"}),
                            html.Div(
                                "Secure patient records powered by Blockchain + IPFS",
                                className="text-muted",
                            ),
                        ],
                        style={"textAlign": "center", "paddingTop": "15px", "paddingBottom": "5px"},
                    ),
                    width=12,
                ),
                className="justify-content-center mt-3 mb-1",
            ),

            # 🔹 Floating layout: Left - Center - Right
            dbc.Row(
                [
                    dbc.Col(left_info, xs=12, md=3, lg=3, className="mb-4"),
                    dbc.Col(form_card, xs=12, md=6, lg=4, className="mb-4"),
                    dbc.Col(right_info, xs=12, md=3, lg=3, className="mb-4"),
                ],
                justify="center",
                align="center",
                className="mt-3",
            ),

            # Footer
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.Span("Built with 💡 IPFS & Blockchain "),
                        ],
                        className="text-center text-muted small",
                        style={"paddingTop": "10px", "paddingBottom": "30px"},
                    ),
                    width=12,
                )
            ),
        ],
        fluid=True,
        style={
            "minHeight": "100vh",
            "background": "linear-gradient(135deg, #e0f7fa 0%, #80deea 100%)",
            "paddingTop": "10px",
        },
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
