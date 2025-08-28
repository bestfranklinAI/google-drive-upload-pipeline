from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError
from typing import Dict, List
import io
import logging
from upload.google_drive import main_upload

logger = logging.getLogger(__name__)

class DriveClient:
    def __init__(self, creds_path: str):
        scopes = ['https://www.googleapis.com/auth/drive']
        try:
            creds = service_account.Credentials.from_service_account_file(
                creds_path, scopes=scopes
            )
            self.service = build(
                'drive', 'v3', credentials=creds, cache_discovery=False
            )
            logger.info('Connected to Google Drive')
        except Exception as exc:
            logger.exception('Failed to connect to Google Drive')
            raise

    def get_start_page_token(self) -> str:
        resp = self.service.changes().getStartPageToken(
            supportsAllDrives=True
        ).execute()
        return resp.get('startPageToken')

    def list_changes(self, page_token: str, include_removed: bool = True) -> Dict:
        logger.info('Fetching changes from Google Drive')
        return self.service.changes().list(
            pageToken=page_token,
            includeRemoved=include_removed,
            spaces='drive',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

    def get_revisions(self, file_id: str) -> List[Dict]:
        resp = self.service.revisions().list(
            fileId=file_id,
            # supportsAllDrives=True,
        ).execute()
        return resp.get('revisions', [])

    def get_file_metadata(self, file_id: str) -> Dict:
        return self.service.files().get(
            fileId=file_id,
            fields='id,name,mimeType',
            supportsAllDrives=True,
        ).execute()

    def download_revision(self, file_id: str, revision_id: str) -> bytes:
        request = self.service.revisions().get_media(
            fileId=file_id,
            revisionId=revision_id,
            supportsAllDrives=True,
        )
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()

    def export_google_file(self, file_id: str, mime_type: str) -> str:
        request = self.service.files().export(
            fileId=file_id,
            mimeType=mime_type,
            supportsAllDrives=True,
        )
        return request.execute().decode('utf-8')

    def upload_file(self, folder_id: str, path: str):
        main_upload(
            local_dir=path,
            drive_id=folder_id,
            client_secret='client_secret.json'
        )