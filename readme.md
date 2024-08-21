# Automated Minestrator SFTP Backup System

This Python script automates the process of downloading files from an SFTP server, zipping the downloaded files, and then uploading the zip file to a remote server. It also notifies designated recipients via email with a link to the backup. It is mostly made to backup minestrator minecraft servers.

## Features

- **Automated Backup**: Downloads files from a specified SFTP server at a target time every day.
- **File Compression**: Compresses the downloaded files into a zip archive.
- **Remote Upload**: Uploads the compressed file to a file hosting service.
- **Email Notifications**: Sends an email with the download link to specified recipients.
- **Customizable Configurations**: Easily configure SFTP, SMTP, and other settings through a JSON configuration file.

## Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/FH-DEV1/Daily-SFTP-server-backup.git
    cd backup-script
    ```

2. **Install Dependencies**:
    Ensure you have Python installed, then install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure Settings**:
    Create a `config.json` file in the root directory of the project. Use the following structure:

    ```json
    {
        "sftp": {
          "host": "your_sftp_host",
          "port": your_sftp_port,
          "username": "your_sftp_username",
          "password": "your_sftp_password",
          "remote_dir": "/path/to/remote/dir",
          "local_dir": "./backup"
        },
        "smtp": {
          "server": "your_smtp_server",
          "port": your_smtp_port,
          "user": "your_email_address",
          "password": "your_email_password"
        },
        "ignore_folders": [
          ".cache",
          "cache",
          "libraries",
          "logs"
        ],
        "email_recipients": [
          "recipient1@example.com",
          "recipient2@example.com"
        ],
        "target_time": "05:00"
    }
    ```

4. **Run the Script**:
    Execute the script to start the backup process:
    ```bash
    python main.py
    ```

## Usage

- **SFTP Connection**: The script connects to the SFTP server using the credentials specified in `config.json`.
- **Download and Compress**: It downloads the contents of the specified remote directory, ignoring folders listed in `ignore_folders`, and compresses the contents into a zip file.
- **Upload**: The zip file is uploaded to a remote file hosting service.
- **Email Notification**: An email is sent to the recipients listed in `email_recipients` with the download link to the backup file.

## Configuration Options

- **`target_time`**: The time of day (in 24-hour format) when the backup should start. Ensure that the server running the script is set to the correct timezone.
- **`ignore_folders`**: List of folder names that should be ignored during the backup process.

## Logging

The script provides color-coded console output to indicate different log levels:
- **Info** (Cyan): General operational messages.
- **Success** (Green): Indicates successful operations like file downloads, zipping, and email sending.
- **Warning** (Yellow): Warnings, such as skipped folders.
- **Error** (Red): Any errors that occur during the backup process.

## Contribution

Feel free to submit issues or pull requests if you have any improvements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

