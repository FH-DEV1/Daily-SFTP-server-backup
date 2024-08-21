import os, paramiko, zipfile, shutil, requests, smtplib, json, pytz
from datetime import datetime, timedelta
from time import sleep
from email.mime.text import MIMEText

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# SFTP connection details
HOST = config['sftp']['host']
PORT = config['sftp']['port']
USERNAME = config['sftp']['username']
PASSWORD = config['sftp']['password']
REMOTE_DIR = config['sftp']['remote_dir']
LOCAL_DIR = config['sftp']['local_dir']

# SMTP server settings
smtp_server = config['smtp']['server']
smtp_port = config['smtp']['port']
smtp_user = config['smtp']['user']
smtp_password = config['smtp']['password']

# List of folders to ignore
IGNORE_FOLDERS = config['ignore_folders']

# Email recipients list
EMAIL_RECIPIENTS = config['email_recipients']

target_time = datetime.strptime(config['target_time'], "%H:%M").time()

paris_tz = pytz.timezone('Europe/Paris')

def color_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

def log_message(message, level="info"):
    colors = {
        "info": "36",      # Cyan
        "success": "32",   # Green
        "warning": "33",   # Yellow
        "error": "31",     # Red
    }
    color = colors.get(level, "36")  # Default to Cyan for info

    # Use Paris timezone in logs
    colored = color_text(f'[{datetime.now(paris_tz).strftime("%Y-%m-%d %H:%M:%S %Z%z")}]', color)
    print(f"{colored} {message}")

def cleanup_old_backups(prefix="backup"):
    """Remove any existing zip files with names starting with the specified prefix."""
    for filename in os.listdir("./"):
        if filename.startswith(prefix) and filename.endswith(".zip"):
            file_path = os.path.join("./", filename)
            log_message(f"Removing old backup file: {file_path}", "warning")
            os.remove(file_path)
            log_message(f"Old backup file removed: {file_path}", "success")

def sftp_download_recursive(sftp, remote_path, local_path):
    os.makedirs(local_path, exist_ok=True)
    for item in sftp.listdir(remote_path):
        remote_item = os.path.join(remote_path, item).replace('\\', '/')
        local_item = os.path.join(local_path, item)
        
        # Skip ignored folders
        if item in IGNORE_FOLDERS:
            log_message(f"Skipping folder: {remote_item}", "warning")
            continue
        
        if _is_directory(sftp, remote_item):
            log_message(f"Entering directory: {remote_item}", "info")
            sftp_download_recursive(sftp, remote_item, local_item)
        else:
            log_message(f"Downloading file: {remote_item} to {local_item}", "info")
            sftp.get(remote_item, local_item)

def _is_directory(sftp, path):
    try:
        return paramiko.SFTPAttributes.from_stat(sftp.stat(path)).st_mode & 0o40000 == 0o40000
    except IOError:
        return False

def zip_folder(folder_path, zip_name):
    """Zip the entire folder."""
    zip_filename = f"{zip_name}.zip"
    log_message(f"Zipping folder: {folder_path} to {zip_filename}", "info")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    log_message(f"Folder zipped successfully: {zip_filename}", "success")
    return zip_filename

def delete_folder(folder_path):
    """Delete the folder after zipping."""
    log_message(f"Deleting folder: {folder_path}", "info")
    shutil.rmtree(folder_path)
    log_message("Folder deleted successfully.", "success")

def main():
    log_message(f"Backup service started. Waiting for {config['target_time']}...", "info")
    while True:
        now = datetime.now(paris_tz)
        if now.time() >= target_time and now.time() < (datetime.combine(now.date(), target_time, paris_tz) + timedelta(minutes=1)).time():
            # Clean up old backup files
            cleanup_old_backups()

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())          
            try:
                ssh.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD)
                sftp = ssh.open_sftp()
                log_message("Connection successfully established.", "success")
                sftp_download_recursive(sftp, REMOTE_DIR, LOCAL_DIR)
                log_message("All files and folders have been downloaded.", "success")
                
                # Zip the downloaded backup
                zip_name = f"backup_{datetime.now(paris_tz).strftime('%d-%m-%Y')}"
                zip_file = zip_folder(LOCAL_DIR, zip_name)
                log_message(f"Zip file created: {zip_file}", "info")
                
                # Delete the unzipped folder
                delete_folder(LOCAL_DIR)
                
            finally:
                sftp.close()
                ssh.close()

            get_serv_url = "https://api.gofile.io/servers?zone=eu"
            serv_name = json.loads(requests.request("GET", get_serv_url).text)["data"]["servers"][0]["name"]
            log_message(f"Uploading to {serv_name}", "info")
            url = f"https://{serv_name}.gofile.io/contents/uploadfile"
            files=[
            ('file',(zip_file,open(zip_file,'rb'),'application/zip'))
            ]
            response = json.loads(requests.request("POST", url, files=files).text)["data"]["downloadPage"]

            log_message(f"Backup URL: {response}", "success")
            date = datetime.now(paris_tz).strftime("%d/%m/%Y")
            try:
                smtp_connection = smtplib.SMTP(smtp_server, smtp_port)
                smtp_connection.starttls()  # Secure the connection
                smtp_connection.login(smtp_user, smtp_password)
                
                # Send email to all recipients
                for recipient in EMAIL_RECIPIENTS:
                    email_body = f"The backup of the {date} is available for a limited time at: {response}"
                    email_message = MIMEText(email_body)
                    email_message["Subject"] = f"Server Backup {date}"
                    email_message["From"] = smtp_user
                    email_message["To"] = recipient
                    smtp_connection.sendmail(smtp_user, recipient, email_message.as_string())
                    log_message(f"Email sent successfully to {recipient}!", "success")
            finally:
                smtp_connection.quit()  # Close the connection
                log_message("Backup process completed. Waiting for the next day.", "info")
            sleep(60)
        sleep(30)

if __name__ == "__main__":
    main()
