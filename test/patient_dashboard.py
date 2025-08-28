import json
import sys, os
from dash import Dash, html, Input, Output, dcc
import dcc.Location
import dash_bootstrap_components as dbc
from uuid import uuid4
import ipfshttpclient
from dash.dependencies import Input, Output, State, MATCH




BLOCKCHAIN_FILE = "blockchain.json"        

# 🌐 Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "Patient Dashboard"




#  Load blockchain from file
def load_blockchain():
    try:
        with open(BLOCKCHAIN_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except:
        pass
    return []




def fetch_from_ipfs(cid):
    try:
        client = ipfshttpclient.connect()
        raw_data = client.cat(cid)
        metadata = json.loads(raw_data.decode("utf-8"))

        layout = []

        # Display metadata cleanly
        layout.append(html.H4("📄 Metadata", style={"marginTop": "10px"}))
        for key in ["filename", "patient_name","patient_id", "patient_name","file_type", "timestamp", "disease", "description", "file-status", "next-appointment", "doctor", "uploaded_by"]:
            if key in metadata:
                layout.append(
                    html.Div([
                        html.Strong(f"{key.replace('_', ' ').capitalize()}: "),
                        str(metadata[key])
                    ])
                )

        # Guess MIME type from filename
        filename = metadata.get("filename", "")
        ext = filename.lower().split(".")[-1]
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
            # Add more preview types here if needed

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




#  Extract patient records from blockchain
def get_patient_records(patient_id):
    chain = load_blockchain()
    records = []
    for block in chain:
        if not isinstance(block, dict):
            continue  # Skip malformed blocks
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




# 🧱 Layout
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    html.H2("👤 Patient Dashboard", className="my-4"),
    html.Div(id="patient-id-display", className="mb-3"),
    html.Button("🔄 Refresh Records", id="refresh-btn", className="mb-3 btn btn-primary"),
    html.Div(id="records-container")
], fluid=True)






# 🚀 Display patient data when refresh button is clicked
@app.callback(
    Output("records-container", "children"),
    [Input("url", "search"),
     Input("refresh-btn", "n_clicks")],
    prevent_initial_call=False
)
def display_patient_data(search, _):
    if not search or "?pid=" not in search:
        return html.Div("❌ Patient ID not provided.", className="alert alert-danger")

    patient_id = search.split("?pid=")[-1]
    records = get_patient_records(patient_id)

    if not records:
        return html.Div("⚠️ No records found for this patient.", className="alert alert-warning")

    cards = []
    for record in records:
        preview = fetch_from_ipfs(record["cid"])
        card = dbc.Card([
            dbc.CardHeader(f"📦 Block #{record['block_index']} — {record['timestamp']}"),
            dbc.CardBody([
                html.P(f"🗂 File Type: {record["file_type"]}"),
                html.P(f"🩺 Disease: {record['disease']}"),
                html.P(f"⌛ File Status: {"Open" if record['file_status'] else "Closed"}"),
                html.P(f"📤 Uploaded By: {record["uploaded_by"]}"),
                html.Button("🔍 View File", id={'type': 'preview-toggle', 'cid': record['cid']}, className="btn btn-info btn-sm mb-2"),
                dbc.Collapse(
                    fetch_from_ipfs(record['cid']),
                    id={'type': 'preview-collapse', 'cid': record['cid']},
                    is_open=False
                )
            ])
        ], className="mb-3 shadow-sm")
        cards.append(card)

    return cards




# Show patient ID above records
@app.callback(
    Output("patient-id-display", "children"),
    Input("url", "search"),
    prevent_initial_call=False
)
def show_patient_id(search):
    if not search or "?pid=" not in search:
        return ""
    patient_id = search.split("?pid=")[-1]
    return html.H5(f"🔎 Viewing Records for Patient ID: {patient_id}")




# callback to toogle the cid view (fetch from IPFS)
@app.callback(
    Output({'type': 'preview-collapse', 'cid': MATCH}, 'is_open'),
    Input({'type': 'preview-toggle', 'cid': MATCH}, 'n_clicks'),
    State({'type': 'preview-collapse', 'cid': MATCH}, 'is_open'),
    prevent_initial_call=True
)
def toggle_file_preview(n_clicks, is_open):
    return not is_open if n_clicks else is_open




if __name__ == "__main__":
    app.run(debug=True, port=8051)
