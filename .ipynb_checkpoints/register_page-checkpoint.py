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
    """
    Register layout with floating info cards (left & right of register card).
    """

    #  Register Card (center)
    form_card = dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.H2("📝 Create Account", className="mb-1 fw-bold"),
                        html.Div(
                            "Join MedRecords and securely manage your blockchain-backed records.",
                            className="text-muted mb-3",
                        ),
                    ],
                    style={"textAlign": "left"},
                ),

                dbc.Label("Username", html_for="reg-username", className="small fw-semibold"),
                dbc.Input(
                    id="reg-username",
                    type="text",
                    placeholder="Enter username",
                    className="mb-3",
                ),

                dbc.Label("Patient ID", html_for="reg-patient-id", className="small fw-semibold"),
                dbc.Input(
                    id="reg-patient-id",
                    type="text",
                    placeholder="Patient ID (only if patient)",
                    className="mb-3",
                ),

                dbc.Label("Password", html_for="reg-password", className="small fw-semibold"),
                dbc.Input(
                    id="reg-password",
                    type="password",
                    placeholder="Enter password",
                    className="mb-3",
                ),

                dbc.Button(
                    "Register",
                    id="register-button",
                    color="success",
                    className="w-100 mb-2",
                ),

                html.Div(id="register-message", className="text-danger text-center mb-2"),

                dbc.Button(
                    "Already have an account? Login",
                    id="to-login",
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
                html.H5("Why register?", className="fw-bold text-primary mb-3"),
                dbc.ListGroup(
                    [
                        dbc.ListGroupItem("📂 Manage personal medical records"),
                        dbc.ListGroupItem("🔑 Secure access anytime"),
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
                html.H5("Benefits", className="fw-bold text-primary mb-3"),
                dbc.ListGroup(
                    [
                        dbc.ListGroupItem("🌍 Decentralized IPFS storage"),
                        dbc.ListGroupItem("⚡ Blockchain security"),
                    ],
                    flush=True,
                    className="small rounded-3 shadow-sm",
                ),
                html.Div(
                    [
                        dbc.Badge("Privacy-first", color="secondary", className="me-2"),
                        dbc.Badge("Blockchain", color="success", className="me-2"),
                        dbc.Badge("IPFS", color="info"),
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
                                "Your secure gateway to blockchain + IPFS medical data",
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
