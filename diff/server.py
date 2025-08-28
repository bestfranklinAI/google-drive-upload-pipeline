import time
import logging
from fastapi import FastAPI
from typing import Optional
from pathlib import Path
from datetime import datetime

from .config import load_config
from .drive_client import DriveClient
from .logger import append_jsonl
from .scheduler import schedule_job
from .diff_service import unified_diff

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
start_time = time.time()
config = load_config()
drive = DriveClient(config.credentials_path)


def _revision_diff(file_id: str, old_rev: str, new_rev: str, mime: str) -> str:
    try:
        old_bytes = drive.download_revision(file_id, old_rev)
        new_bytes = drive.download_revision(file_id, new_rev)
        try:
            old_text = old_bytes.decode('utf-8')
            new_text = new_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return ''
        return unified_diff(old_text, new_text)
    except Exception as exc:
        logger.error('Failed to diff revisions for %s: %s', file_id, exc)
        return ''

changelog_path = Path('changelog.jsonl')
token_path = Path('page_token.txt')

page_token: Optional[str] = None
if token_path.exists():
    page_token = token_path.read_text().strip() or None
    logger.info('Loaded saved page token')
last_sync: Optional[str] = None


def init_page_token():
    global page_token
    logger.info('Initializing start page token')
    page_token = drive.get_start_page_token()
    token_path.write_text(page_token)


def process_changes():
    global page_token, last_sync
    if not page_token:
        init_page_token()
    changes = drive.list_changes(page_token)
    changelog_path.touch(exist_ok=True)
    change_list = changes.get('changes', [])
    logger.info('Processing %d change(s)', len(change_list))
    if not change_list:
        logger.info('No changes detected')
    for change in change_list:
        logger.debug('Raw change: %s', change)
        file_id = change.get('fileId')
        file_name = change.get('file', {}).get('name')
        logger.info('Processing change for %s', file_name)
        removed = change.get('removed', False) or change.get('file', {}).get('trashed', False)
        event_type = 'delete' if removed else 'update'
        diff = None
        if not removed and file_id:
            revisions = drive.get_revisions(file_id)
            if len(revisions) <= 1:
                event_type = 'create'
            if len(revisions) >= 2:
                latest = revisions[-1]
                prev = revisions[-2]
                mime = latest.get('mimeType', '')
                diff = _revision_diff(file_id, prev['id'], latest['id'], mime)
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'fileId': file_id,
            'fileName': file_name,
            'eventType': event_type,
        }
        if diff:
            event['diff'] = diff
        append_jsonl(changelog_path, event)
    if 'newStartPageToken' in changes:
        page_token = changes['newStartPageToken']
        token_path.write_text(page_token)
    last_sync = datetime.utcnow().isoformat()
    if config.upload_enabled:
        drive.upload_file(config.folder_id, str(changelog_path))
        logger.info('Changelog uploaded')
    else:
        logger.info('Upload disabled; changelog kept locally')
    logger.info('Finished processing changes')


@app.on_event('startup')
def startup_event():
    logger.info('Starting scheduler with %d second interval', config.poll_interval)
    schedule_job(config.poll_interval, process_changes)
    logger.info('Scheduler started')
    logger.info('Running initial sync')
    process_changes()


@app.get('/status')
def status():
    return {
        'uptime': time.time() - start_time,
        'lastSync': last_sync,
        'lastToken': page_token,
    }


@app.post('/trigger')
def trigger():
    logger.info('Manual trigger received')
    process_changes()
    return {'status': 'triggered'}
