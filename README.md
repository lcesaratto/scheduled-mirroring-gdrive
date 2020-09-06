# AutoSyncDrive

This script allows an user to copy all the information in the desired local folders to a google drive folder as a periodic backup.
Credentials and Client Secrets must be added in the proyect directory.

Python version <= 3.7.9



In powershell: Set-ExecutionPolicy Unrestricted
python -m venv venv
venv\scripts\activate.bat
pip install -r requirements.txt
pyinstaller --add-data "client_secrets.json;." --add-data "settings.yaml;." --add-data "credentials.txt;." --add-data "data_to_config;data_to_config" --add-data "google_drive_resources;." --onefile --windowed backup.py



For Startup/Shutdown:
Run gpedit.msc (Local Policies)
Computer Configuration -> Windows Settings -> Scripts -> Startup or Shutdown -> Properties -> Add

For Logon/Logoff:
Run gpedit.msc (Local Policies)
User Configuration -> Windows Settings -> Scripts -> Logon or Logoff -> Properties -> Add