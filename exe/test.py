import win32com.client

def rtf_to_docx(rtf_path, docx_path):
    word = win32com.client.Dispatch("Word.Application")
    doc = word.Documents.Open(rtf_path)
    doc.SaveAs(docx_path, FileFormat=16)  # 16 = wdFormatDocumentDefault (docx)
    doc.Close()
    word.Quit()

# Example usage
rtf_to_docx(r"C:\Users\6122060\Downloads\AIML\XML Track Changes\Chapter conversion\Forms\Bound Volumes--Styled RTF\exe\Input\FLPRFMS 10 TRACKING & REVISIONS (revision copy).rtf", r"C:\Users\6122060\Downloads\AIML\XML Track Changes\Chapter conversion\Forms\Bound Volumes--Styled RTF\exe\Output\FLPRFMS 10 TRACKING & REVISIONS (revision copy).docx")



def rtf_to_docx(rtf_path, docx_path):


    pythoncom.CoInitialize()
    rtf_path = os.path.abspath(rtf_path)
    docx_path = os.path.abspath(docx_path)
    print(f"RTF Path: {rtf_path}")
    print(f"DOCX Path: {docx_path}")
    if not os.path.exists(rtf_path):
        raise FileNotFoundError(f"File not found: {rtf_path}")
    time.sleep(0.2)  # Optional: Give time for disk flush if just saved
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(rtf_path)
        doc.SaveAs(docx_path, FileFormat=16)
        doc.Close()
    except Exception as e:
        raise RuntimeError(f"Failed to convert: {e}")
    finally:
        word.Quit()

if __name__ == "__main__":
    # Import your main conversion functions
    # from your_module import process_docx, handle_entities

    st.set_page_config(
        page_title="Track Changes RTF/DOCX to XML Converter",
        page_icon="📄",  # Professional document icon
        layout="wide",
        initial_sidebar_state="collapsed",  # Sidebar collapsed by default
    )

    # Custom CSS for a professional, clean look
    st.markdown("""
        <style>
        body, .reportview-container {
            background: #f7f7f7;
            color: #222;
            font-family: "Segoe UI", "Arial", sans-serif;
        }
        .sidebar .sidebar-content {
            background: #f2f2f2;
        }
        .stButton>button, .stDownloadButton>button {
            background-color: #ff9800;
            color: white;
            border-radius: 4px;
            font-size: 16px;
            font-weight: 500;
            padding: 0.4em 1.5em;
            border: none;
            transition: background 0.2s;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background-color: #fb8c00;
        }
        h1, h2, h3, h4 {
            color: #222;
            font-family: "Segoe UI", "Arial", sans-serif;
            font-weight: 600;
        }
        .stMarkdown {
            color: #444;
        }
        .status-ok {
            color: #388e3c;
            font-weight: 500;
        }
        .status-fail {
            color: #d32f2f;
            font-weight: 500;
        }
        .file-table td, .file-table th {
            padding: 0.5em 1em;
            font-size: 15px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Track Changes RTF/DOCX → XML Converter")
    st.markdown(
        """
        <h4>Convert your Word/RTF files with tracked changes into structured XML, fast.</h4>
        <p>Upload multiple files. Each will be processed and available for download.</p>
        """,
        unsafe_allow_html=True
    )

    uploaded_files = st.file_uploader(
        "Upload RTF or DOCX files",
        type=["docx", "rtf"],
        accept_multiple_files=True,
        help="Supports multiple files with track changes."
    )

    if uploaded_files:
        st.markdown("<h4>Processing Results</h4>", unsafe_allow_html=True)
        results_table = []
        for idx, uploaded_file in enumerate(uploaded_files):
            with st.spinner(f"Processing file {idx+1}/{len(uploaded_files)}: {uploaded_file.name}"):
                temp_dir = "temp_files"
                temp_folder = "temp_folder"  # Folder for converted DOCX files from RTF

                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                if not os.path.exists(temp_folder):
                    os.makedirs(temp_folder)


                temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                # Ensure file is written and closed before next step
                temp_file_path = os.path.abspath(temp_file_path)
                print(f"Saved file to: {temp_file_path}")
                assert os.path.exists(temp_file_path), f"File does not exist after writing: {temp_file_path}"
                
                file_ext = os.path.splitext(uploaded_file.name)[1].lower()

                if file_ext == ".rtf":
                    # Store converted DOCX in temp_folder
                    converted_docx_path = os.path.join(
                        temp_folder,
                        os.path.splitext(uploaded_file.name)[0] + ".docx"
                    )
                    try:
                        rtf_to_docx(temp_file_path, converted_docx_path)
                        docx_path = converted_docx_path
                    except Exception as e:
                        st.markdown(
                            f"<div class='status-fail'>❌ {uploaded_file.name} failed to convert RTF to DOCX: {e}</div>",
                            unsafe_allow_html=True
                        )
                        continue  # Skip this file
                else:
                    # For DOCX uploads, process from temp_dir
                    docx_path = temp_file_path

                try:
                    whole_text = process_docx(docx_path)
                    # ... (rest of your XML processing and Streamlit UI code)
                except Exception as e:
                    st.markdown(
                        f"<div class='status-fail'>❌ {uploaded_file.name} failed: {e}</div>",
                        unsafe_allow_html=True
                    )
    else:
        st.info("Please upload one or more RTF or DOCX files.", icon="📄")

    st.markdown(
        """
        <hr>
        <small style="color:#888;">
        <b>Note:</b> This tool is optimized for legal and technical documents. All conversions are handled securely and locally.
        </small>
        """,
        unsafe_allow_html=True
    )