import subprocess
import webbrowser
import sys
import time
import os
import socket

def porta_ativa(porta=8501):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", porta)) == 0

# Caminho absoluto do app (funciona mesmo após virar .exe)
base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
app_file = os.path.join(base_dir, "dashboard_app_sqlite.py")

PORT = 8501
URL = f"http://localhost:{PORT}"

if porta_ativa(PORT):
    webbrowser.open(URL)
else:
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", app_file,
                      f"--server.port={PORT}", "--server.headless=true"])
    time.sleep(5)
    webbrowser.open(URL)
