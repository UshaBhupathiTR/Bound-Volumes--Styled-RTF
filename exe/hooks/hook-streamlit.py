from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.utils.hooks import collect_data_files

# This hook tells PyInstaller to include all Streamlit's data files.
datas = collect_data_files("streamlit")

# This is a crucial step to correctly bundle Streamlit's package metadata.
datas += copy_metadata("streamlit")
