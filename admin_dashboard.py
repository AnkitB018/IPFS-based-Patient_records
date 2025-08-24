# admin_dashboard.py
import json
import os
import re
import base64
from datetime import datetime

import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State, MATCH
import dash_bootstrap_components as dbc
import ipfshttpclient

from Blockchain import Blockchain  # your existing blockchain implementation


# ---------------------
# Helper functions
# ---------------------
def fetch_from_ipfs(cid):
    """
    Fetch metadata JSON stored in IPFS under cid and return dash/html layout.
    (Same behaviour as before, wrapped in nicer layout.)
    """
    try:
        client = ipfshttpclient.connect()
        raw_data = client.cat(cid)
        metadata = json.loads(raw_data.decode("utf-8"))

        layout = []

        # Display metadata cleanly
        layout.append(html.H5("📄 Metadata", style={"marginTop": "10px"}))
        for key in ["filename", "patient_name", "patient_id", "file_type", "timestamp", "disease", "description", "file-status", "next-appointment", "doctor", "uploaded_by"]:
            if key in metadata:
                layout.append(
                    html.Div([
                        html.Strong(f"{key.replace('_', ' ').capitalize()}: "),
                        html.Span(str(metadata[key]))
                    ], style={"marginBottom": "6px"})
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
            layout.append(html.Hr())
            if ext in ["jpg", "jpeg", "png", "gif"]:
                layout.append(html.H6("🖼️ Image Preview"))
                layout.append(
                    html.Img(
                        src=f"data:{mime_type};base64,{file_data}",
                        style={"maxWidth": "100%", "borderRadius": "6px"}
                    )
                )
            elif ext == "pdf":
                layout.append(html.H6("📑 PDF Preview"))
                layout.append(
                    html.Iframe(
                        src=f"data:application/pdf;base64,{file_data}",
                        style={"width": "100%", "height": "520px", "border": "1px solid #ddd", "borderRadius": "6px"}
                    )
                )

            # Download Button
            layout.append(html.Hr())
            layout.append(
                html.A(
                    "⬇️ Download File",
                    href=f"data:{mime_type};base64,{file_data}",
                    download=filename or "file",
                    target="_blank",
                    style={
                        "display": "inline-block",
                        "marginTop": "8px",
                        "padding": "8px 16px",
                        "backgroundColor": "#0d6efd",
                        "color": "white",
                        "borderRadius": "6px",
                        "textDecoration": "none",
                    }
                )
            )

        return layout

    except Exception as e:
        return html.Div(f"❌ IPFS Error: {e}", style={"color": "red"})


def render_chain(chain):
    cols = []
    for block in chain[-10:]:
        card = dbc.Card(
            dbc.CardBody([
                html.H6(f"🧱 Block #{block.index}", style={"marginBottom": "6px"}),
                html.Div(f"Timestamp: {block.timestamp}", className="small text-muted mb-1"),
                html.Div(f"Hash: {block.hash}", className="small text-truncate mb-1"),
                html.Div(f"Prev: {block.previous_hash}", className="small text-truncate mb-1"),
                html.Div(f"Nonce: {block.nonce}", className="small text-muted mb-2"),
                html.Hr(),
                # Data preview with max height + scroll
                html.Div(
                    html.Pre(json.dumps(block.data, indent=2), style={"margin": 0}),
                    style={"backgroundColor": "#f8f9fa", "padding": "8px", "borderRadius": "6px", "maxHeight": "220px", "overflow": "auto"}
                )
            ]),
            className="mb-3 shadow-sm"
        )
        cols.append(dbc.Col(card, xs=12, md=6, lg=4))

    return dbc.Row(cols, className="g-3")


# Layout wrapper function
def layout(username):
    header = html.Div(
        [
            html.Span(f"Welcome, {username} (Admin)", style={"fontSize": "16px", "fontWeight": 600, "color": "white"}),
            dbc.Button("Logout", id="logout-admin-button", n_clicks=0, size="sm",
                       style={"backgroundColor": "white", "color": "#0d9488", "border": "none",
                              "padding": "6px 12px", "borderRadius": "999px"})
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "width": "100%",
            "padding": "10px 16px",
            "backgroundColor": "#0ea5a4",   # teal
            "borderRadius": "8px",
        }
    )
    # Add Data tab (keeps original upload IDs)
    add_data_card = dbc.Card(
        dbc.CardBody([
            html.Div([
                html.H5("📤 Upload and Add to Blockchain", className="mb-2"),
                html.Div("Upload a report (PDF/image/Excel). Metadata will be stored on IPFS and a reference saved in the blockchain.", className="small text-muted mb-3")
            ]),
            dcc.Upload(
                id="upload-data",
                children=html.Div(["Drag and Drop or ", html.A("Select a File")]),
                style={
                    "width": "100%",
                    "height": "70px",
                    "lineHeight": "70px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "6px",
                    "textAlign": "center",
                    "marginBottom": "12px",
                },
                multiple=False
            ),

            html.Div(id="upload-status", style={"marginBottom": "8px", "fontWeight": "bold", "color": "green"}),

            dbc.Row([
                dbc.Col(dbc.Label("Patient Name", className="small fw-semibold"), md=4),
                dbc.Col(dbc.Label("Patient ID", className="small fw-semibold"), md=4),
                dbc.Col(dbc.Label("File Type", className="small fw-semibold"), md=4)
            ], className="mb-2"),

            dbc.Row([
                dbc.Col(dcc.Input(id="patient-name", type="text", placeholder="Name of Patient", style={"width": "100%"}), md=4),
                dbc.Col(dcc.Input(id="patient-id", type="text", placeholder="Patient ID", style={"width": "100%"}), md=4),
                dbc.Col(dcc.Input(id="file-type", type="text", placeholder="File Type", style={"width": "100%"}), md=4)
            ], className="mb-3"),

            dbc.Row([
                dbc.Col(dcc.Input(id="description", type="text", placeholder="Summary / Description", style={"width": "100%"}), md=6),
                dbc.Col(dcc.Input(id="disease", type="text", placeholder="Identified Disease", style={"width": "100%"}), md=6)
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("File Status", className="small"),
                    dcc.Dropdown(
                        id="file-status",
                        options=[{"label": "Open", "value": True}, {"label": "Closed", "value": False}],
                        value=True,
                        style={"width": "100%"}
                    )
                ], md=4),
                dbc.Col([
                    dbc.Label("Next Appointment", className="small"),
                    dcc.DatePickerSingle(id="next-appointment", display_format="YYYY-MM-DD", placeholder="Select Date", style={"width": "100%"})
                ], md=4),
                dbc.Col([
                    dbc.Label("Doctor", className="small"),
                    dcc.Input(id="doctor", type="text", placeholder="Doctor in charge", style={"width": "100%"})
                ], md=4)
            ], className="mb-3"),

            dbc.Row([
                dbc.Col(dbc.Label("Uploaded By", className="small"), md=6),
                dbc.Col(html.Div(className="small text-muted"), md=6)
            ]),
            dbc.Row([
                dbc.Col(dcc.Input(id="uploader", type="text", placeholder="Uploaded By", style={"width": "100%"}), md=6),
                dbc.Col(html.Div(), md=6)
            ], className="mb-3"),

            html.Div(style={"textAlign": "center"},
                     children=[dbc.Button("Add to Blockchain", id="submit-btn", n_clicks=0, color="primary")]),

            html.Div(id="upload-output", style={"color": "green", "marginTop": "12px", "fontSize": "14px"})
        ]),
        className="shadow-sm",
        style={"padding": "14px", "borderRadius": "8px", "backgroundColor": "white", "maxWidth": "100%"}
    )

    # View Blocks tab
    view_blocks_card = dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.H5("🔍 View Last Ten Blocks on Blockchain", className="mb-0"), md=8),
                dbc.Col(html.Div([dbc.Badge("Live", color="success")], className="text-end"), md=4)
            ], className="align-items-center mb-2"),
            html.Div(html.Button("🔄 View Blocks", id="view-chain-btn", n_clicks=0, style={"marginTop": "10px"}), style={"marginBottom": "12px"}),
            html.Hr(),
            html.H6("🔍 View Blocks using Patient ID", className="mb-2"),
            dbc.Row([
                dbc.Col(dcc.Input(id="P-ID", type="text", placeholder="Enter Patient Id here", style={"width": "100%"}), md=8),
                dbc.Col(dbc.Button("🔄 View Blocks", id="view-ID-Blocks", n_clicks=0, color="secondary", style={"width": "100%"}), md=4)
            ], className="mb-3"),
            html.Div(id="chain-container")
        ]),
        className="shadow-sm",
        style={"padding": "14px", "borderRadius": "8px", "backgroundColor": "white"}
    )

    # Fetch by CID tab
    fetch_card = dbc.Card(
        dbc.CardBody([
            html.H5("📦 Fetch File from IPFS by CID", className="mb-2"),
            html.Div("Paste CID of metadata JSON and fetch preview/download.", className="small text-muted mb-2"),
            dbc.Row([
                dbc.Col(dcc.Input(id="cid-input", type="text", placeholder="Enter CID here", style={"width": "100%"}), md=9),
                dbc.Col(dbc.Button("Fetch", id="fetch-btn", n_clicks=0, color="primary", style={"width": "100%"}), md=3)
            ], className="mb-3"),
            html.Div(id="ipfs-output", style={"whiteSpace": "pre-wrap", "marginTop": "8px"})
        ]),
        className="shadow-sm",
        style={"padding": "14px", "borderRadius": "8px", "backgroundColor": "white"}
    )

    tabs = dbc.Tabs(
        [
            dbc.Tab(add_data_card, label="Add Data", tab_id="tab-add"),
            dbc.Tab(view_blocks_card, label="View Blocks", tab_id="tab-view"),
            dbc.Tab(fetch_card, label="Fetch by CID", tab_id="tab-fetch"),
        ],
        active_tab="tab-add",
        className="mb-3"
    )

    # Outer: centered content so cards don't stretch too wide
    return dbc.Container([
        header,
        html.Br(),
        dbc.Row(
            dbc.Col(
                html.Div([
                    html.H2("Admin Dashboard", style={"textAlign": "center", "marginBottom": "8px"}),
                    html.Div("Manage uploads, inspect blockchain and fetch IPFS contents.", className="text-center text-muted mb-3"),
                    tabs
                ]),
                width={"size": 10, "offset": 1}
            )
        )
    ], fluid=True, style={"minHeight": "100vh", "background": "linear-gradient(135deg, #e0f7fa 0%, #80deea 100%)", "paddingTop": "12px"})


# Wrapper function for all the callbacks
def register_admin_callbacks(app):

    # callback to notify if a file is uploaded or not before submit
    @app.callback(
        Output("upload-status", "children"),
        Input("upload-data", "filename")
    )
    def show_upload_status(filename):
        if filename:
            return f"✅ File uploaded: {filename}"
        return "❌ No file selected"


    # callback for disabling and enabling next-appointment
    @app.callback(
        Output("next-appointment", "disabled"),
        Input("file-status", "value"),
        prevent_initial_call=True
    )
    def diable_enable(key):
        if key == False:
            return True
        else:
            return False


    # Combined: get Id specific blocks (preserves original Output allow_duplicate usage)
    @app.callback(
        Output("chain-container", "children", allow_duplicate=True),
        Input("view-ID-Blocks", "n_clicks"),
        State("P-ID", "value"),
        prevent_initial_call=True
    )
    def Chain_on_id(n_clicks, ID):
        if n_clicks == 0:
            return []
        chain = Blockchain().chain
        cols = []
        for block in chain:
            if isinstance(block.data, dict) and block.data.get("patient ID") == ID:
                card = dbc.Card(
                    dbc.CardBody([
                        html.H6(f"🧱 Block #{block.index}", style={"marginBottom": "6px"}),
                        html.Div(f"Timestamp: {block.timestamp}", className="small text-muted"),
                        html.Div(f"Hash: {block.hash}", className="small text-truncate"),
                        html.Div(f"Previous Hash: {block.previous_hash}", className="small text-truncate"),
                        html.Div(f"Nonce: {block.nonce}", className="small text-muted"),
                        html.Hr(),
                        html.Div(
                            html.Pre(json.dumps(block.data, indent=2), style={"margin": 0}),
                            style={"backgroundColor": "#f8f9fa", "padding": "8px", "borderRadius": "6px", "maxHeight": "220px", "overflow": "auto"}
                        )
                    ]),
                    className="mb-3"
                )
                cols.append(dbc.Col(card, xs=12, md=6, lg=4))

        if not cols:
            return dbc.Alert("No blocks found for that Patient ID.", color="warning")

        return dbc.Row(cols, className="g-3")


    # view the last 5 chain
    @app.callback(
        Output("chain-container", "children", allow_duplicate=True),
        Input("view-chain-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def update_chain(n_clicks):
        if n_clicks == 0:
            return []
        chain = Blockchain().chain
        return render_chain(chain)


    # To view a specific block from cid
    @app.callback(
        Output("ipfs-output", "children"),
        Input("fetch-btn", "n_clicks"),
        State("cid-input", "value"),
        prevent_initial_call=True
    )
    def fetch_ipfs_content(n_clicks, cid):
        if not cid:
            return "Please enter a CID."
        if not re.match(r"^[a-zA-Z0-9]{46,}$", cid):
            return "❌ Invalid CID format."

        return fetch_from_ipfs(cid)


    # For logout (clear session and redirect to /login)
    @app.callback(
        Output("session-store", "data", allow_duplicate=True),
        Output("url", "pathname", allow_duplicate=True),
        Input("logout-admin-button", "n_clicks"),
        prevent_initial_call=True
    )
    def logout(n_clicks):
        if n_clicks:
            return {}, "/login"
        return dash.no_update, dash.no_update


    # Add data to chain
    @app.callback(
        Output("upload-output", "children"),
        Input("submit-btn", "n_clicks"),
        State("upload-data", "contents"),
        State("upload-data", "filename"),
        State("patient-name", "value"),
        State("patient-id", "value"),
        State("file-type", "value"),
        State("uploader", "value"),
        State("description", "value"),
        State("disease", "value"),
        State("file-status", "value"),
        State("next-appointment", "date"),
        State("doctor", "value"),
        prevent_initial_call=True
    )
    def upload_to_blockchain(n_clicks, contents, filename, patient_name, patient_id, file_type, uploader, description, disease, file_status, nex_appointment, doctor):
        if n_clicks == 0:
            return ""

        # Check required fields (file and description are optional)
        if not (patient_id and file_type and uploader and disease and doctor):
            return "❌ Please fill all required fields (Patient ID, File Type, Uploader, Disease, Doctor)."

        # Build the metadata dictionary
        metadata = {
            "filename": filename if filename else "N/A",
            "patient_id": patient_id,
            "file_type": file_type,
            "patient_name": patient_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": description if description else "No description provided.",
            "disease": disease,
            "file-status": "Open" if file_status else "Closed",
            "next-appointment": nex_appointment,
            "doctor": doctor,
            "uploaded_by": uploader,
        }

        # If a file is uploaded, decode and embed base64
        if contents and filename:
            try:
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                metadata["file_base64"] = base64.b64encode(decoded).decode('utf-8')
            except Exception as e:
                return f"❌ Failed to process uploaded file: {e}"

        # Save metadata to temp file and upload to IPFS
        try:
            with open("temp_metadata.json", "w") as f:
                json.dump(metadata, f)

            client = ipfshttpclient.connect()
            res = client.add("temp_metadata.json")
            cid = res['Hash']
            os.remove("temp_metadata.json")

            # Store only minimal info in blockchain
            data = {
                "Patient Name": patient_name,
                "patient ID": patient_id,
                "File Type": file_type,
                "Disease": disease,
                "File Status": "Open" if file_status else "Closed",
                "cid": cid,
                "Uploaded By": uploader,
                "Timestamp": metadata["timestamp"]
            }

            # Add to blockchain
            chain = Blockchain()
            chain.add_block(data)

            return f"✅ Metadata uploaded to IPFS (CID: {cid}) and reference stored in blockchain."

        except Exception as e:
            if os.path.exists("temp_metadata.json"):
                os.remove("temp_metadata.json")
            return f"❌ Upload failed: {e}"
