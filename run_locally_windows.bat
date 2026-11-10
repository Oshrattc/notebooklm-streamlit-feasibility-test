@echo off
rem Starts the public test page on THIS computer only (http://localhost:8503), never on the network.
cd /d "%~dp0"
python -m streamlit run streamlit_app.py --server.port 8503 --server.address localhost --browser.gatherUsageStats false
pause
