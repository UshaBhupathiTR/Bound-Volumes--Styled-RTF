import streamlit.web.cli as stcli
import os
import sys

def resolve_path(path):
    # This ensures PyInstaller can find your main app file
    if getattr(sys, "frozen", False):
        # The application is frozen
        return os.path.join(sys._MEIPASS, path)
    
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path)
    return os.path.abspath(os.path.join(os.getcwd(), path))
if __name__ == "__main__":
    # The --global.developmentMode=false flag is important
    # to prevent errors with metadata checks.
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())
