@echo off
REM Caminho do Python do ambiente virtual
SET PYTHON="%~dp0.venv\Scripts\python.exe"

REM Executa o dashboard
%PYTHON% "%~dp0\run_dashboard.py"

REM Mantém o terminal aberto em caso de erro
pause

