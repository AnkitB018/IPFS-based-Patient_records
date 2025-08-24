import json
import os
from dash import html, dcc, no_update
import dash_bootstrap_components as dbc
import ipfshttpclient
from dash.dependencies import Input, Output, State, MATCH

BLOCKCHAIN_FILE = "blockchain.json"
USERS_FILE = "users.json"


# Helper functions
def load_blockchain():
    try:
        with open(BLOCKCHAIN_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except:
        pass
    return []




def get_patient_id_from_username(username):
    try:
        if not os.path.exists(USERS_FILE):
            return None
        with open(USERS_FILE, "r") as f:
            users = json.load(f)

        # Case 1: dict keyed by username
        if isinstance(users, dict):
            return users.get(username, {}).get("patient_id")

        # Case 2: list of dicts
        if isinstance(users, list):
            for u in users:
                if u.get("username") == username:
                    return u.get("patient_id")
    except Exception:
        pass
    return None




def fetch_from_ipfs(cid):
    try:
        client = ipfshttpclient.connect()
        raw_data = client.cat(cid)
        metadata = json.loads(raw_data.decode("utf-8"))

        layout = []
        layout.append(html.H4("📄 Metadata", style={"marginTop": "10px"}))
        for key in ["filename", "patient_name", "patient_id", "file_type", "timestamp",
                    "disease", "description", "file-status", "next-appointment", "doctor", "uploaded_by"]:
            if key in metadata:
                layout.append(
                    html.Div([
                        html.Strong(f"{key.replace('_', ' ').capitalize()}: "),
                        str(metadata[key])
                    ])
                )

        # Guess MIME type from filename
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

        # File preview
        if file_data:
            if ext in ["jpg", "jpeg", "png", "gif"]:
                layout.append(html.Hr())
                layout.append(html.H4("🖼️ Image Preview"))
                layout.append(
                    html.Img(
                        src=f"data:{mime_type};base64,{file_data}",
                        style={"maxWidth": "500px", "marginTop": "10px"}
                    )
                )
            elif ext == "pdf":
                layout.append(html.Hr())
                layout.append(html.H4("📑 PDF Preview"))
                layout.append(
                    html.Iframe(
                        src=f"data:application/pdf;base64,{file_data}",
                        style={"width": "100%", "height": "600px", "border": "1px solid #ccc"}
                    )
                )

            layout.append(html.Hr())
            layout.append(
                html.A(
                    "⬇️ Download File",
                    href=f"data:{mime_type};base64,{file_data}",
                    download=filename or "file",
                    target="_blank",
                    style={
                        "display": "inline-block",
                        "marginTop": "15px",
                        "padding": "10px 20px",
                        "backgroundColor": "#007BFF",
                        "color": "white",
                        "borderRadius": "5px",
                        "textDecoration": "none",
                    }
                )
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
    return records


# Layout function
def layout(username=None):
    header_text = f"👤 Patient Dashboard — {username}" if username else "👤 Patient Dashboard"
    return dbc.Container([
        #logout button
        dbc.Navbar(
          dbc.Container([
                html.Span(header_text, className= "navbar-brand mb-0 h1", style = {"color": "white"}),
                dbc.Button(
                    "Logout", id= "logout-button", color= "danger", className= "ms-auto", n_clicks = 0
                )
          ], fluid= True),
           color = "dark",
           dark = True,
           className= "mb-4" 
        ),

        html.Div(id="patient-id-display", className="mb-3"),
        html.Button("🔄 Refresh Records", id="refresh-btn", className="mb-3 btn btn-primary"),
        html.Div(id="records-container")
    ], fluid=True)



# Callback wrapper function
def register_patient_callbacks(app):
    """
    Must be called from app.py with the main `app` instance:
        patient_dashboard.register_patient_callbacks(app)
    """

    @app.callback(
        Output("records-container", "children"),
        Input("refresh-btn", "n_clicks"),
        State("session-store", "data"),
        prevent_initial_call=False
    )
    def display_patient_data(n_clicks, session_data):
        # Determine patient_id from session (preferred) or fallback to error
        if not session_data or not session_data.get("username"):
            return html.Div("❌ Not logged in. Please login to view records.", className="alert alert-danger")

        username = session_data.get("username")
        patient_id = get_patient_id_from_username(username)
        if not patient_id:
            return html.Div("❌ Patient ID not found for this user.", className="alert alert-danger")

        records = get_patient_records(patient_id)
        if not records:
            return html.Div("⚠️ No records found for this patient.", className="alert alert-warning")

        cards = []
        for record in records:
            # Fixed f-string quoting usage
            card = dbc.Card([
                dbc.CardHeader(f"📦 Block #{record['block_index']} — {record['timestamp']}"),
                dbc.CardBody([
                    html.P(f"🗂 File Type: {record['file_type']}"),
                    html.P(f"🩺 Disease: {record['disease']}"),
                    html.P(f"⌛ File Status: {'Open' if record['file_status'] else 'Closed'}"),
                    html.P(f"📤 Uploaded By: {record['uploaded_by']}"),
                    html.Button("🔍 View File", id={'type': 'preview-toggle', 'cid': record['cid']},
                                className="btn btn-info btn-sm mb-2"),
                    dbc.Collapse(
                        fetch_from_ipfs(record['cid']),
                        id={'type': 'preview-collapse', 'cid': record['cid']},
                        is_open=False
                    )
                ])
            ], className="mb-3 shadow-sm")
            cards.append(card)

        return cards

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
        return html.H5(f"🔎 Viewing Records for Patient ID: {patient_id}")

    @app.callback(
        Output({'type': 'preview-collapse', 'cid': MATCH}, 'is_open'),
        Input({'type': 'preview-toggle', 'cid': MATCH}, 'n_clicks'),
        State({'type': 'preview-collapse', 'cid': MATCH}, 'is_open'),
        prevent_initial_call=True
    )
    def toggle_file_preview(n_clicks, is_open):
        return not is_open if n_clicks else is_open

    
    @app.callback(
        Output("session-store", "data", allow_duplicate= True),
        Output("url", "pathname", allow_duplicate=True),
        Input("logout-button", "n_clicks"),
        prevent_initial_call=True
    )
    def logout_user(n_clicks):
        if n_clicks:
            return {}, "/login"
        return no_update, no_update
