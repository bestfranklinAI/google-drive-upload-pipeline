import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]



def authenticate_gdrive(client_secret: str):
    """
    Handles Google Drive API authentication.
    """
    creds = None
    # Ensure we load tokens relative to this script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Modified: get current script directory
    token_path = os.path.join(script_dir, "secrets", "token.json")  # Modified: token path relative to script
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(script_dir, client_secret), SCOPES
            )  # Modified: client_secret path relative to script
            creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(token_path), exist_ok=True)  # Modified: ensure directory exists
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return creds


def upload_folders_and_markdown(client_secret, local_folder_path, drive_folder_id="root"):
    """
    Recursively uploads only folders and .md files to Google Drive.

    Args:
        local_folder_path (str): Path to local folder.
        drive_folder_id (str): Destination Drive folder ID.
    """
    creds = authenticate_gdrive(client_secret)
    uploaded = []

    try:
        service = build("drive", "v3", credentials=creds)

        for name in os.listdir(local_folder_path):
            path = os.path.join(local_folder_path, name)

            if os.path.isdir(path):
                # Create folder in Drive
                folder_meta = {
                    'name': name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [drive_folder_id]
                }
                folder = service.files().create(body=folder_meta, fields='id').execute()
                print(f"Directory '{name}' created (ID: {folder['id']})")
                uploaded.extend(
                    upload_folders_and_markdown(client_secret, path, folder['id'])
                )

            elif os.path.isfile(path) and name.lower().endswith('.md'):
                # Upload markdown file
                print(f"Uploading markdown: {name}...")
                meta = {
                    'name': name,
                    'parents': [drive_folder_id]
                }
                media = MediaFileUpload(path, mimetype='text/markdown', resumable=True)
                f = service.files().create(
                    body=meta, media_body=media, fields='id, name'
                ).execute()
                print(f"Uploaded '{f['name']}' (ID: {f['id']})")
                uploaded.append(f)

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

    return uploaded


# Modified: Added 'replace' parameter defaulting to False
# when replace=True, existing contents of the target drive folder will be deleted
# if replace=False, new folder is created alongside existing content

def main_upload(local_dir: str,
                drive_id: str,
                client_secret: str = "secrets/client_secret.json",
                replace: bool = False):  # Modified: Added replace param
    """
    Main function to upload folders and markdown files.
    
    Args:
        local_dir (str): Local directory to upload.
        drive_id (str): Google Drive folder ID (parent).
        replace (bool): If True, delete everything in drive_id before uploading.
    """
    # Check local directory exists
    if not os.path.exists(local_dir):
        print(f"Local directory '{local_dir}' does not exist.")
        return

    # Authenticate and build Drive service
    creds = authenticate_gdrive(client_secret)
    service = build("drive", "v3", credentials=creds)

    # Modified: Handle replace logic
    if replace:
        print(f"Replace=True: Deleting all contents inside Drive folder ID '{drive_id}'...")
        # List and delete all files/folders in the target drive folder
        page_token = None
        while True:
            response = service.files().list(
                q=f"'{drive_id}' in parents",
                fields="nextPageToken, files(id, name)",
                pageToken=page_token
            ).execute()
            for file in response.get('files', []):
                service.files().delete(fileId=file['id']).execute()
                print(f"Deleted '{file['name']}' (ID: {file['id']})")
            page_token = response.get('nextPageToken', None)
            if not page_token:
                break

    # Modified: Create a new top-level folder matching the local folder name
    folder_name = os.path.basename(local_dir.rstrip(os.sep))
    print(f"Creating new folder '{folder_name}' in Drive folder ID '{drive_id}'...")
    folder_meta = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [drive_id]
    }
    folder = service.files().create(body=folder_meta, fields='id').execute()
    new_folder_id = folder['id']
    print(f"Folder '{folder_name}' created (ID: {new_folder_id})")

    # Proceed to recursive upload into the new folder
    print(f"Starting upload from '{local_dir}' to Drive folder ID '{new_folder_id}'...")
    results = upload_folders_and_markdown(client_secret, local_dir, new_folder_id)
    if results is not None:
        print(f"Upload completed. {len(results)} items uploaded.")
    else:
        print("Upload failed.")


if __name__ == '__main__':
    # Example usage:
    LOCAL_DIR = "path/to/local/folder"
    DRIVE_ID = "your_drive_folder_id"
    GOOGLE_CLIENT_SECRET = "secrets/client_secret.json"
    # Modified: pass replace=True or False as needed
    main_upload(LOCAL_DIR, DRIVE_ID, GOOGLE_CLIENT_SECRET, replace=False)
