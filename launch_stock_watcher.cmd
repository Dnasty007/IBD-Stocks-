@echo off
setlocal
set "PROJECT_HOME=%~dp0"
set "HOME=%PROJECT_HOME%"
set "USERPROFILE=%PROJECT_HOME%"
"%PROJECT_HOME%\.venv\Scripts\python.exe" -m streamlit run "%PROJECT_HOME%\app.py" --server.headless true --server.port 8504
