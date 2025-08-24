import dash
from dash import html, dcc, Input, Output, State
import json
import os
import ipfshttpclient
from datetime import datetime
from Blockchain import Blockchain
import base64
import re





#helpter functions

def fetch_from_ipfs(cid):
    try:
        client = ipfshttpclient.connect()
        raw_data = client.cat(cid)
        metadata = json.loads(raw_data.decode("utf-8"))

        layout = []

        # Display metadata cleanly
        layout.append(html.H4("📄 Metadata", style={"marginTop": "10px"}))
        for key in ["filename", "patient_name","patient_id", "file_type", "timestamp", "disease", "description", "file-status", "next-appointment", "doctor", "uploaded_by"]:
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





def render_chain(chain):
    blocks = []
    for block in chain[-5:]:
        blocks.append(
            html.Div([
                html.H4(f"🧱 Block #{block.index}", style={"marginBottom": "5px"}),
                html.Div(f"Timestamp: {block.timestamp}"),
                html.Div(f"Hash: {block.hash}"),
                html.Div(f"Previous Hash: {block.previous_hash}"),
                html.Div(f"Nonce: {block.nonce}"),
                html.Pre(json.dumps(block.data, indent=2), style={"backgroundColor": "#f0f0f0", "padding": "10px"}),
                html.Hr()
            ])
        )
    return blocks
    
# End of helper function






#layout wrapper function
def layout(username):
    return html.Div([
        
        html.Div([
            html.H2(f"welcome, {username} (Admin)", style= {"margin": 0, "textAlign": "center"}),
            html.Button(
                "Logout", id="logout-admin-button", n_clicks= 0, style= {"backgroundColor": "#dc3545", "color": "white", "border": "none", "padding": "8px 16px", "cursor": "pointer", "borderRadius": "5px"}
            )
        ], style= {"display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "marginBottom": "20px",
            "padding": "10px",
            "backgroundColor": "#343a40", 
            "color": "white"}),
        
        
        html.Div([
            html.H2("Admin Dashboard", style={"textAlign":"center"}),
            html.Div([
    
        html.H1("🧬 IPFS-Integrated Blockchain Viewer", style={"textAlign": "center"}),

        #For adding data to blockchain
        html.H2("📤 Upload and Add to Blockchain", style={"marginTop": "30px", "textAlign": "center"}),

        #add a file(text currently like pdf, excel)
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Label("Upload Document", style={"marginBottom": "10px", "fontWeight": "bold"}),
                        dcc.Upload(
                            id="upload-data",
                            children=html.Div([
                                "Drag and Drop or ", html.A("Select a File")
                            ]),
                            style={
                                "width": "100%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "marginBottom": "20px",
                            },
                            multiple=False
                        ),
                    ],
                    style={
                        "width": "300px",  # Adjust width here as needed
                        "textAlign": "center",
                    }
                )
            ],
            style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "marginTop": "20px"
            }
        ),

        #To show the status of file upload
        html.Div(id="upload-status", style={"marginBottom": "20px", "fontWeight": "bold", "color": "green", "display": "flex", "justifyContent": "center"}),
            
            
        #input div 1 for patient name, id, file-type
        html.Div([
            #For name of patient
            html.Div([
                html.Label("Enter the Name of Patient:  "),
                dcc.Input(id="patient-name", type="text", placeholder= "Name of Patient", style={"marginRight": "10px"})
            ], style = {"width": "30%", "marginRight": "20px"}),

            #For id of patient
            html.Div([
                html.Label("Enter Associated Patient ID:  "),
                dcc.Input(id="patient-id", type="text", placeholder="Patient ID", style={"marginRight": "10px"})
            ], style = {"width": "30%", "marginRight": "20px"}),

            html.Div([
                html.Label("Enter Type of File: "),
                dcc.Input(id="file-type", type="text", placeholder="File Type", style={"marginRight": "10px"})
            ], style = {"width": "30%"})
        ], style={"display": "flex", "flexWrap": "wrap", "marginBottom": "15px", "justifyContent": "center"}),
 

            
        #input div 2 for description and disease
        html.Div([
            #for description
            html.Div([
                html.Label("Enter Summery if any: "),
                dcc.Input(id="description", type = "text", placeholder = "Description", style={"marginRight": "10px"})
            ], style = {"width": "30%", "marginRight": "20px"}),

            #for disease
            html.Div([
                html.Label("Enter Identified Disease: "),
                dcc.Input(id="disease", type="text", placeholder = "disease", style = {"marginRight": "10px"})
            ], style = {"width": "30%"})
            
        ], style={"display": "flex", "flexWrap": "wrap", "marginBottom": "15px", "justifyContent": "center"}),
    

        #input div 3 for status and next date
        html.Div([
            #for file status
            html.Div([
                html.Label("Enter File Status:  "),
                dcc.Dropdown(
                    id = "file-status",
                    options = [
                        {"label": "Open", "value": True},
                        {"label": "Closed", "value": False},
                    ],
                    placeholder = "File Status?",
                    value = True,
                    style = {"width":"70%"}
                )
            ], style = {"display": "flex", "alignItems": "center", "marginBottom": "15px", "width": "30%", "marginRight": "20px"}),
    
            #for next appointment date
            html.Div([
                html.Label("Enter Next Appointment Date: "),
                dcc.DatePickerSingle(
                    id="next-appointment",
                    placeholder="Select Date",
                    display_format="YYYY-MM-DD",  
                    style={"marginRight": "20px"}
                )
            ], style = {"display": "flex", "alignItems": "center", "marginBottom": "15px", "width": "30%"})
        ], style = {"display": "flex", "flexWrap": "wrap", "marginBottom": "15px", "justifyContent": "center"}),
    
        html.Br(),
            
        #input div 4 (last) for doctor and uploader
        html.Div([
            #for the name of doctor
            html.Div([
                html.Label("Name of Doctor in Charge: "),
                dcc.Input(id="doctor", type="text", placeholder="Doctor in charge", style={"marginRight": "10px"})
            ], style = {"width": "30%", "marginRight": "20px"}),
    
            #for the name of uploader
            html.Div([
                html.Label("Enter Uploader: "),
                dcc.Input(id="uploader", type="text", placeholder="Uploaded By",  style={"marginRight": "10px"})
            ], style = {"width": "30%"})
        ], style={"display": "flex", "flexWrap": "wrap", "marginBottom": "20px", "justifyContent": "center"}),
        
        html.Br(),
         
        #button to upload all the information provided
        html.Div(
            html.Button("Add to Blockchain", id="submit-btn", n_clicks=0, style={"marginTop": "10px", "padding": "10px 20px"}),
            style = { "textAlign": "center", "marginTop": "20px"}
        ),
    
    
    
        #show if successful or faced any error
        html.Div(id="upload-output", style={"color": "green", "marginTop": "20px"}),
    
        html.Br(),
        html.Br(),
        html.Hr(),
            
    





        #For data in blocks viewing
        html.Div([
            #For viewing last 5 block data in blockchain 
            html.Div([
                html.H2("🔍 View Last five Blocks on Blockchain", style={"marginTop": "30px"}),
                html.Button("🔄 View Blocks", id="view-chain-btn", n_clicks=0)         
            ], style = { "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center", "marginTop": "40px", "marginRight":"40px"}),
    
            #For viewing ID specific Blocks in Blockchain
            html.Div([
                html.H2("🔍 View Blocks using Patient ID", style= {"marginTop": "30px", "marginBottom": "10px"}),
                html.Div([
                     dcc.Input(id = "P-ID", type = "text", placeholder= "Enter Patient Id here", style= {"marginRight": "5px", "marginBottom": "15px"}),
                     html.Button("🔄 View Blocks", id="view-ID-Blocks", n_clicks=0, style= {"width": "30%"}) 
                ], style = {"display": "flex", "flexWrap": "wrap", "marginBottom": "20px", "justifyContent": "center"})
            ], style = { "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center", "marginTop": "40px", "marginLeft": "40px"})
        ], style = {"display": "flex", "flexWrap": "wrap", "marginBottom": "20px", "justifyContent": "center"}),
    



            
        #show chain data here
        html.Div(id="chain-container"),
        
                
        #view specific block and get to IPFS using CID
        html.H2("📦 Fetch File from IPFS by CID", style={"marginTop": "50px"}),
        dcc.Input(id="cid-input", type="text", placeholder="Enter CID here", style={"width": "400px"}),
        html.Button("Fetch", id="fetch-btn", n_clicks=0, style={"marginLeft": "10px"}),
        html.Pre(id="ipfs-output", style={"whiteSpace": "pre-wrap", "marginTop": "20px"}),
    
        html.Div("", style={"marginBottom": "100px"})
    ])
        ])
        ])






# wrapper functiton for all the callbacks 
def register_admin_callbacks(app):

    #callback to notify if a file is uploaded or not before submit
    @app.callback(
        Output("upload-status", "children"),
        Input("upload-data", "filename")
    )
    def show_upload_status(filename):
        if filename:
            return f"✅ File uploaded: {filename}"
        return "❌ No file selected"







    #callback for disabling and enabling next-appointment
    @app.callback(
        Output("next-appointment", "disabled"),
        Input("file-status", "value"),
        prevent_initial_call = True
    )
    def diable_enable(key):
        if key == False:
            return True
        else: 
            return False


    # get Id specific blocks
    @app.callback(
        Output("chain-container", "children", allow_duplicate=True),
        Input("view-ID-Blocks", "n_clicks"),
        State("P-ID", "value"),
        prevent_initial_call = True
    )
    def Chain_on_id(n_clicks, ID):
        if n_clicks ==0:
            return []
        chain = Blockchain().chain
        blocks = []
        for block in chain:
            if isinstance(block.data, dict) and block.data.get("patient ID") == ID:
                blocks.append(
                    html.Div([
                        html.H4(f"🧱 Block #{block.index}", style={"marginBottom": "5px"}),
                        html.Div(f"Timestamp: {block.timestamp}"),
                        html.Div(f"Hash: {block.hash}"),
                        html.Div(f"Previous Hash: {block.previous_hash}"),
                        html.Div(f"Nonce: {block.nonce}"),
                        html.Pre(json.dumps(block.data, indent=2), style={"backgroundColor": "#f0f0f0", "padding": "10px"}),
                        html.Hr()
                    ]))
            
        return blocks
                





    #view the last 5 chain
    @app.callback(
        Output("chain-container", "children", allow_duplicate=True),
        Input("view-chain-btn", "n_clicks"),
        prevent_initial_call = True
    )
    def update_chain(n_clicks):
        if n_clicks == 0:
            return []
        chain = Blockchain().chain
        return render_chain(chain)







    #To view a specific block from cid
    @app.callback(
        Output("ipfs-output", "children"),
        Input("fetch-btn", "n_clicks"),
        State("cid-input", "value"),
        prevent_initial_call = True
    )
    def fetch_ipfs_content(n_clicks, cid):
        if not cid:
            return "Please enter a CID."
        if not re.match(r"^[a-zA-Z0-9]{46,}$", cid):
            return "❌ Invalid CID format."

        return fetch_from_ipfs(cid)




    # For logout
    @app.callback(
        Output("session-store", "data", allow_duplicate= True),
        Output("url", "pathname", allow_duplicate=True),  # allow_duplicate since other callbacks may set URL
        Input("logout-admin-button", "n_clicks"),
        prevent_initial_call=True
    )
    def logout(n_clicks):
        if n_clicks:
            return {}, "/login"  # Redirect to login page
        return dash.no_update, dash.no_update



 

    
    # Add data to chain
    @app.callback(
        Output("upload-output", "children"),
        Input("submit-btn", "n_clicks"),
        State("upload-data", "contents"),
        State("upload-data", "filename"),
        State("patient-name","value"),
        State("patient-id", "value"),
        State("file-type", "value"),
        State("uploader", "value"),
        State("description", "value"),
        State("disease", "value"),
        State("file-status", "value"),
        State("next-appointment", "date"),
        State("doctor", "value"),
        prevent_initial_call = True
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

                # Optional: embed file data as base64 (works for images, PDFs, Excel, etc.)
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

    
