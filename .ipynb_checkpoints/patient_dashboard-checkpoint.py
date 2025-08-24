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


# -------------------------
# Helper functions (kept behavior / keys same as before)
# -------------------------
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
    """
    Fetch a metadata JSON stored under the given CID from IPFS.
    Returns a list of dash/html elements (same behavior as before).
    """
    try:
        client = ipfshttpclient.connect()  # assumes daemon on 127.0.0.1:5001
        raw_data = client.cat(cid)
        metadata = json.loads(raw_data.decode("utf-8"))

        layout = []
        layout.append(html.H5("📄 Metadata", style={"marginTop": "10px"}))

        # keys to display (unchanged)
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

        # preview handling (unchanged behavior)
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
    """
    Read the blockchain file and return records that match patient_id.
    (Keeps the same keys as your previous implementation.)
    """
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
    # sort by timestamp descending if timestamp exists (best-effort)
    def _ts_key(r):
        try:
            return datetime.strptime(r.get("timestamp", "").split(".")[0], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.min
    records.sort(key=_ts_key, reverse=True)
    return records


def get_patient_id_from_username(username):
    """
    Map username -> patient_id reading USERS_FILE (supports list or dict formats).
    Returns None if not found.
    """
    try:
        if not os.path.exists(USERS_FILE):
            return None
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        # If dict keyed by username
        if isinstance(users, dict):
            u = users.get(username)
            if isinstance(u, dict):
                return u.get("patient_id") or u.get("patient id") or u.get("patientID")
            return None
        # If list of dicts
        if isinstance(users, list):
            for u in users:
                if isinstance(u, dict) and u.get("username") == username:
                    return u.get("patient_id") or u.get("patient id") or u.get("patientID")
    except Exception:
        pass
    return None


# -------------------------
# Layout (improved styling, IDs unchanged)
# -------------------------
def layout(username=None):
    header_text = f"👤 Patient Dashboard — {username}" if username else "👤 Patient Dashboard"

    # Left floating info (small)
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

    # Center: main card area
    main = dbc.Card(
        dbc.CardBody([
            # header row with patient id text is shown via separate element (kept id)
            html.Div(id="patient-id-display"),  # kept for callback output

            dbc.Row([
                dbc.Col(html.H4(header_text, className="mb-3"), xs=12),
            ]),

            # Row with Refresh button + Date range picker (NEW)
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

            # container for records (cards generated by callback)
            html.Div(id="records-container")
        ]),
        className="shadow-lg border-0 rounded-4",
        style={"padding": "18px", "backgroundColor": "white"}
    )

    # Right floating info (small)
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

    # Navbar (logout button on right) — keep the logout-button id
    navbar = dbc.Navbar(
        dbc.Container([
            html.Div(header_text, className="navbar-brand mb-0 h4", style={"color": "white"}),
            dbc.Button("Logout", id="logout-button", color="danger", className="ms-auto")
        ], fluid=True),
        color="primary",
        dark=True,
        className="mb-4"
    )

    # Compose container: navbar + floating layout
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
        # matching the blueish theme used earlier
        "background": "linear-gradient(135deg, #90caf9 0%, #bbdefb 100%)",
        "paddingTop": "12px",
        "paddingBottom": "40px"
    })


# -------------------------
# Callbacks (register_patient_callbacks) — IDs & logic preserved
# -------------------------
def register_patient_callbacks(app):
    """
    Register callbacks on the provided Dash `app`.
    Keep all IDs and logic unchanged; UI elements returned are improved styled HTML.
    """

    @app.callback(
        Output("records-container", "children"),
        Input("refresh-btn", "n_clicks"),
        State("session-store", "data"),
        State("date-range", "start_date"),
        State("date-range", "end_date"),
        prevent_initial_call=False
    )
    def display_patient_data(n_clicks, session_data, start_date, end_date):
        # Determine patient_id from session
        if not session_data or not session_data.get("username"):
            return dbc.Alert("❌ Not logged in. Please login to view records.", color="danger")

        username = session_data.get("username")
        patient_id = get_patient_id_from_username(username)
        if not patient_id:
            return dbc.Alert("❌ Patient ID not found for this user.", color="danger")

        records = get_patient_records(patient_id)
        if not records:
            return dbc.Alert("⚠️ No records found for this patient.", color="warning")

        # Filter by date range if provided (start_date/end_date are ISO 'YYYY-MM-DD' strings)
        def in_range(record_ts):
            if not (start_date or end_date):
                return True
            if not record_ts:
                return True
            # try parse date-part from timestamp
            try:
                # accept timestamps like "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
                date_part = record_ts.split()[0]
                rec_date = datetime.strptime(date_part, "%Y-%m-%d").date()
            except Exception:
                # if parsing fails, include the record (safer)
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

        # Build responsive grid of record cards
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
            # clear session and navigate to login
            return {}, "/login"
        return dash.no_update, dash.no_update
