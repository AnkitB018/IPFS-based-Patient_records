# patient_dashboard.py
import os
import json
from dash import html, dcc
from dash.dependencies import Input, Output, State, MATCH
import dash
import dash_bootstrap_components as dbc
from datetime import datetime
import ipfshttpclient

# Files
BLOCKCHAIN_FILE = "blockchain.json"
USERS_FILE = "users.json"








# ---------------- Helper Functions ----------------
def load_blockchain():
    try:
        with open(BLOCKCHAIN_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def fetch_from_ipfs(cid):
    try:
        client = ipfshttpclient.connect()
        raw_data = client.cat(cid)
        metadata = json.loads(raw_data.decode("utf-8"))

        layout = []
        layout.append(html.H5("📄 Metadata", style={"marginTop": "10px"}))

        keys = [
            "filename", "patient_name", "patient_id", "file_type", "timestamp",
            "disease", "description", "file-status", "next-appointment",
            "doctor", "uploaded_by"
        ]
        for key in keys:
            if key in metadata:
                layout.append(
                    html.Div([
                        html.Strong(f"{key.replace('_', ' ').capitalize()}: "),
                        html.Span(str(metadata[key]))
                    ], style={"marginBottom": "6px"})
                )

        filename = metadata.get("filename", "")
        ext = filename.lower().split(".")[-1] if filename else ""
        mime_map = {
            "pdf": "application/pdf",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        mime_type = mime_map.get(ext, "application/octet-stream")
        file_data = metadata.get("file_base64") or metadata.get("image_base64")

        if file_data:
            layout.append(html.Hr())
            if ext in ["jpg", "jpeg", "png", "gif"]:
                layout.append(html.H6("🖼 Image Preview"))
                layout.append(html.Img(src=f"data:{mime_type};base64,{file_data}",
                                       style={"maxWidth": "100%", "borderRadius": "6px"}))
            elif ext == "pdf":
                layout.append(html.H6("📑 PDF Preview"))
                layout.append(html.Iframe(src=f"data:application/pdf;base64,{file_data}",
                                         style={"width": "100%", "height": "600px", "border": "1px solid #ddd"}))

            layout.append(html.Hr())
            layout.append(
                html.A("⬇️ Download File",
                       href=f"data:{mime_type};base64,{file_data}",
                       download=filename or "file",
                       target="_blank",
                       style={
                           "display": "inline-block", "marginTop": "8px",
                           "padding": "8px 16px", "backgroundColor": "#0d6efd",
                           "color": "white", "borderRadius": "6px", "textDecoration": "none"
                       })
            )

        return layout

    except Exception as e:
        return html.Div(f"❌ IPFS Error: {e}", style={"color": "red"})


def get_patient_records(patient_id):
    chain = load_blockchain()
    records = []
    for block in chain:
        if not isinstance(block, dict):
            continue
        data = block.get("data", {})
        if isinstance(data, dict) and data.get("patient ID") == patient_id:
            records.append({
                "cid": data.get("cid", "N/A"),
                "file_type": data.get("File Type", ""),
                "uploaded_by": data.get("Uploaded By", ""),
                "disease": data.get("Disease", ""),
                "timestamp": block.get("timestamp", ""),
                "file_status": data.get("File Status", ""),
                "block_index": block.get("index", -1)
            })

    def _ts_key(r):
        try:
            return datetime.strptime(r.get("timestamp", "").split(".")[0], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.min
    records.sort(key=_ts_key, reverse=True)
    return records


def get_patient_id_from_username(username):
    try:
        if not os.path.exists(USERS_FILE):
            return None
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        if isinstance(users, dict):
            u = users.get(username)
            if isinstance(u, dict):
                return u.get("patient_id") or u.get("patient id") or u.get("patientID")
            return None
        if isinstance(users, list):
            for u in users:
                if isinstance(u, dict) and u.get("username") == username:
                    return u.get("patient_id") or u.get("patient id") or u.get("patientID")
    except Exception:
        pass
    return None








# ---------------- Layout ----------------
def layout(username=None):
    header_text = f"👤 Patient Dashboard — {username}" if username else "👤 Patient Dashboard"

    left_info = dbc.Card(
        dbc.CardBody([
            html.H6("Quick Info", className="fw-bold mb-2"),
            html.Ul([
                html.Li("🔒 Records are immutable"),
                html.Li("🕒 Timestamped history"),
            ], className="small text-muted")
        ]),
        className="shadow-sm border-0 rounded-3",
        style={"backgroundColor": "white"}
    )

    main = html.Div([
        dcc.Tabs(
            id="patient-tabs",
            value="data",
            children=[
                dcc.Tab(label="📑 Data", value="data"),
                dcc.Tab(label="👤 Profile", value="profile"),
            ],
            style={"marginBottom": "16px"}
        ),
        html.Div(id="tab-content")
    ])

    right_info = dbc.Card(
        dbc.CardBody([
            html.H6("Actions", className="fw-bold mb-2"),
            html.Ul([
                html.Li("🔍 View file preview"),
                html.Li("⬇️ Download attachments"),
            ], className="small text-muted")
        ]),
        className="shadow-sm border-0 rounded-3",
        style={"backgroundColor": "white"}
    )

    navbar = dbc.Navbar(
        dbc.Container([
            html.Div(header_text, className="navbar-brand mb-0 h4", style={"color": "white"}),
            dbc.Button("Logout", id="logout-button", color="danger", className="ms-auto")
        ], fluid=True),
        color="primary",
        dark=True,
        className="mb-4"
    )

    return dbc.Container([
        navbar,
        dbc.Row(
            [
                dbc.Col(left_info, xs=12, md=3, lg=3, className="mb-4"),
                dbc.Col(main, xs=12, md=6, lg=6, className="mb-4"),
                dbc.Col(right_info, xs=12, md=3, lg=3, className="mb-4"),
            ],
            justify="center",
            align="center"
        ),
    ], fluid=True, style={
        "minHeight": "100vh",
        "background": "linear-gradient(135deg, #90caf9 0%, #bbdefb 100%)",
        "paddingTop": "12px",
        "paddingBottom": "40px"
    })









# ---------------- Callbacks ----------------
def register_patient_callbacks(app):
    @app.callback(
        Output("records-container", "children"),
        Input("refresh-btn", "n_clicks"),
        State("session-store", "data"),
        State("date-range", "start_date"),
        State("date-range", "end_date"),
        prevent_initial_call=False
    )
    def display_patient_data(n_clicks, session_data, start_date, end_date):
        if not session_data or not session_data.get("username"):
            return dbc.Alert("❌ Not logged in. Please login to view records.", color="danger")

        username = session_data.get("username")
        patient_id = get_patient_id_from_username(username)
        if not patient_id:
            return dbc.Alert("❌ Patient ID not found for this user.", color="danger")

        records = get_patient_records(patient_id)
        if not records:
            return dbc.Alert("⚠️ No records found for this patient.", color="warning")

        def in_range(record_ts):
            if not (start_date or end_date):
                return True
            if not record_ts:
                return True
            try:
                date_part = record_ts.split()[0]
                rec_date = datetime.strptime(date_part, "%Y-%m-%d").date()
            except Exception:
                return True

            if start_date:
                try:
                    s = datetime.strptime(start_date.split("T")[0], "%Y-%m-%d").date()
                except Exception:
                    s = None
            else:
                s = None
            if end_date:
                try:
                    e = datetime.strptime(end_date.split("T")[0], "%Y-%m-%d").date()
                except Exception:
                    e = None
            else:
                e = None

            if s and rec_date < s:
                return False
            if e and rec_date > e:
                return False
            return True

        filtered = [r for r in records if in_range(r.get("timestamp"))]
        if not filtered:
            return dbc.Alert("⚠️ No records found in the selected date range.", color="warning")

        cols = []
        for record in filtered:
            header = dbc.CardHeader(f"📦 Block #{record['block_index']} — {record['timestamp']}")
            body = dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.Div([html.Strong("File Type:"), html.Div(record["file_type"])]), xs=12, md=6),
                    dbc.Col(html.Div([html.Strong("Disease:"), html.Div(record["disease"])]), xs=12, md=6),
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col(html.Div([html.Strong("Status:"), html.Div("Open" if record['file_status'] else "Closed")]), xs=12, md=4),
                    dbc.Col(html.Div([html.Strong("Uploaded By:"), html.Div(record["uploaded_by"])]), xs=12, md=4),
                    dbc.Col(dbc.Button("🔍 View File", id={'type': 'preview-toggle', 'cid': record['cid']},
                                       color="info", size="sm"), xs=12, md=4, className="text-md-end")
                ], className="align-items-center"),
                dbc.Collapse(
                    fetch_from_ipfs(record['cid']),
                    id={'type': 'preview-collapse', 'cid': record['cid']},
                    is_open=False
                )
            ])

            card = dbc.Card([header, body], className="mb-3 shadow-sm")
            cols.append(dbc.Col(card, xs=12, md=12))

        return dbc.Row(cols)

    @app.callback(
        Output("patient-id-display", "children"),
        Input("refresh-btn", "n_clicks"),
        State("session-store", "data"),
        prevent_initial_call=False
    )
    def show_patient_id(n_clicks, session_data):
        if not session_data or not session_data.get("username"):
            return ""
        username = session_data.get("username")
        patient_id = get_patient_id_from_username(username) or username
        return html.H5(f"🔎 Viewing Records for Patient ID: {patient_id}", className="text-muted")

    @app.callback(
        Output({'type': 'preview-collapse', 'cid': MATCH}, 'is_open'),
        Input({'type': 'preview-toggle', 'cid': MATCH}, 'n_clicks'),
        State({'type': 'preview-collapse', 'cid': MATCH}, 'is_open'),
        prevent_initial_call=True
    )
    def toggle_file_preview(n_clicks, is_open):
        return not is_open if n_clicks else is_open

    @app.callback(
        Output("session-store", "data", allow_duplicate=True),
        Output("url", "pathname", allow_duplicate=True),
        Input("logout-button", "n_clicks"),
        prevent_initial_call=True
    )
    def logout_user(n_clicks):
        if n_clicks:
            return {}, "/login"
        return dash.no_update, dash.no_update


    
    # ---------- Profile Tab ----------
    @app.callback(
        Output("tab-content", "children"),
        Input("patient-tabs", "value"),
        State("session-store", "data"),
        prevent_initial_call=False
    )
    def render_tab(tab, session_data):
        username = session_data.get("username") if session_data else None

        if tab == "data":
            return dbc.Card(
                dbc.CardBody([
                    html.Div(id="patient-id-display"),
                    dbc.Row([
                        dbc.Col(
                            dbc.Button("🔄 Refresh Records", id="refresh-btn", color="primary"),
                            xs=12, sm=5, md=4, className="mb-2"
                        ),
                        dbc.Col(
                            dcc.DatePickerRange(
                                id="date-range",
                                start_date_placeholder_text="Start date",
                                end_date_placeholder_text="End date",
                                display_format="YYYY-MM-DD",
                                minimum_nights=0,
                                with_portal=False
                            ),
                            xs=12, sm=7, md=8, className="mb-2"
                        ),
                    ], className="mb-3 align-items-center"),
                    html.Div(id="records-container")
                ]),
                className="shadow-lg border-0 rounded-4",
                style={"padding": "18px", "backgroundColor": "white"}
            )

        elif tab == "profile":
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
            u = users.get(username, {})

            # Personal Info
            personal_section = dbc.Card(
                dbc.CardBody([
                    html.H5("👤 Personal Info", className="mb-3 text-primary"),
                    dbc.Row([
                        dbc.Col(html.Div([html.Strong("Username:"), html.Div(username)]), md=6),
                        dbc.Col(html.Div([html.Strong("Patient ID:"), html.Div(u.get("patient_id","NA"))]), md=6),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText("Full Name"), dbc.Input(id="pi-full-name", value=u.get("full_name","NA"))]), md=6),
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText("Gender"), dbc.Input(id="pi-gender", value=u.get("gender","NA"))]), md=6),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col(
                            dbc.InputGroup([
                                dbc.InputGroupText("Date of Birth"),
                                dbc.Input(
                                    id="pi-dob",
                                    type="date",
                                    value=u.get("date_of_birth", None) if u.get("date_of_birth") != "NA" else None,
                                    placeholder="Select Date of Birth"
                                )
                            ]),
                            md=6
                        ),
                        dbc.Col(
                            dbc.InputGroup([
                                dbc.InputGroupText("Blood Group"),
                                dbc.Input(id="pi-blood", value=u.get("blood_group", "NA"))
                            ]),
                            md=6
                        ),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText("Phone"), dbc.Input(id="pi-phone", value=u.get("phone","NA"))]), md=6),
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText("Email"), dbc.Input(id="pi-email", value=u.get("email","NA"))]), md=6),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText("Address"), dbc.Input(id="pi-address", value=u.get("address","NA"))]), md=12),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText("Emergency Contact Name"), dbc.Input(id="pi-em-name", value=u.get("emergency_contact_name","NA"))]), md=6),
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText("Emergency Contact Phone"), dbc.Input(id="pi-em-phone", value=u.get("emergency_contact_phone","NA"))]), md=6),
                    ], className="mb-2"),
                    dbc.Button("💾 Save Personal Info", id="save-personal-btn", color="primary")
                ]),
                className="mb-4 shadow-sm"
            )

            # Medical Info
            medical_section = dbc.Card(
                dbc.CardBody([
                    html.H5("🏥 Medical Info", className="mb-3 text-success"),
                    dbc.Row([
                        dbc.Col(dbc.Badge(f"Height: {u.get('height','NA')}", color="info", pill=True), md=4),
                        dbc.Col(dbc.Badge(f"Weight: {u.get('weight','NA')}", color="info", pill=True), md=4),
                        dbc.Col(dbc.Badge(f"BMI: {u.get('bmi','NA')}", color="info", pill=True), md=4),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col(dbc.Alert(f"Blood Pressure: {u.get('blood_pressure','NA')}", color="secondary"), md=6),
                        dbc.Col(dbc.Alert(f"Heart Rate: {u.get('heart_rate','NA')}", color="secondary"), md=6),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col(html.Div([html.Strong("Allergies:"), html.Div(u.get("allergies","NA"))]), md=6),
                        dbc.Col(html.Div([html.Strong("Chronic Conditions:"), html.Div(u.get("chronic_conditions","NA"))]), md=6),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col(html.Div([html.Strong("Current Medications:"), html.Div(u.get("current_medications","NA"))]), md=6),
                        dbc.Col(html.Div([html.Strong("Past Surgeries:"), html.Div(u.get("past_surgeries","NA"))]), md=6),
                    ], className="mb-2"),
                ]),
                className="shadow-sm border-success",
                style={"borderLeft": "6px solid #28a745"}
            )

            return dbc.Card(
                dbc.CardBody([personal_section, medical_section]),
                className="shadow-lg border-0 rounded-4",
                style={"padding": "18px", "backgroundColor": "white"}
            )

        return dbc.Alert("⚠️ Unknown tab selected.", color="warning")

    
    # Save personal info
    @app.callback(
        Output("save-personal-btn", "children"),
        Input("save-personal-btn", "n_clicks"),
        State("session-store", "data"),
        State("pi-full-name", "value"),
        State("pi-gender", "value"),
        State("pi-dob", "value"),
        State("pi-blood", "value"),
        State("pi-phone", "value"),
        State("pi-email", "value"),
        State("pi-address", "value"),
        State("pi-em-name", "value"),
        State("pi-em-phone", "value"),
        prevent_initial_call=True
    )
    def save_personal_info(n_clicks, session_data, full_name, gender, dob ,blood_group, phone, email, address, em_name, em_phone):
        if not session_data or not session_data.get("username"):
            return "❌ Save Failed"
        username = session_data["username"]

        try:
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
            if username in users:
                users[username]["full_name"] = full_name
                users[username]["gender"] = gender
                users[username]["blood_group"] = blood_group
                users[username]["phone"] = phone
                users[username]["email"] = email
                users[username]["address"] = address
                users[username]["emergency_contact_name"] = em_name
                users[username]["emergency_contact_phone"] = em_phone
                users[username]["date_of_birth"] = dob
                with open(USERS_FILE, "w") as f:
                    json.dump(users, f, indent=2)
            return "✅ Saved!"
        except Exception as e:
            return f"❌ Error: {e}"
