@echo off  
cd /d "%%~dp0"  
start /min cmd /k "python leitor.py"  
start cmd /k "python -m streamlit run painel.py" 
