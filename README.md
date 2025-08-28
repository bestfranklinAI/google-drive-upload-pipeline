
# Google Drive Activity Log

This application monitors a Google Drive folder for changes and writes a changelog with event details and diffs between file revisions.

## 📥 Getting `client_secrets.json` from Google Cloud Console

1. **Create a new project**  
   - Open the **Google Cloud Console** → **IAM & Admin** → **Create a project**.  
   - Give the project a name and note the *Project ID*.

2. **Enable the Google Drive API**  
   - In the left navigation, select **APIs & Services → Library**.  
   - Search for **Google Drive API** and click **Enable**.

3. **Configure the OAuth consent screen**  
   - Go to **APIs & Services → OAuth consent screen**.  
   - Choose **External** (or **Internal** if you are on a G Suite domain).  
   - Fill the required fields. In the **Testing** section, add **your own email address** (or any tester) as a *Tester* and save.

4. **Create OAuth client credentials**  
   - Navigate to **APIs & Services → Credentials** → **Create credentials → OAuth client ID**.  
   - Select **Desktop app** (or **Web application** if you prefer) and give it a name.  
   - Click **Create**, then **Download JSON**.

5. **Place the JSON file in the project**  
   - In the repository root, create a folder named `secrets` (if it doesn’t exist).  
   - Move the downloaded file into `secrets/` and rename it to `client_secrets.json`.

6. **Reference the credentials in your environment**  
   Add (or update) the following line in your `.env` file:

   ```env
   GOOGLE_APPLICATION_CREDENTIALS=./secrets/client_secrets.json
   ```

> **⚠️ Security note** – Add `secrets/` to `.gitignore` to keep the credential file out of version control.

## Development

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Create a `.env` file in the project root**

   ```env
   GOOGLE_APPLICATION_CREDENTIALS=./secrets/client_secrets.json
   FOLDER_ID=your_folder_id
   POLL_INTERVAL=300
   UPLOAD_ENABLED=true
   ```

   - `FOLDER_ID` – ID of the Drive folder you want to monitor.  
   - `POLL_INTERVAL` – Seconds between each poll (default = 300).  
   - `UPLOAD_ENABLED` – Set to `false` to skip uploading the changelog to Drive.

   **Important:** The target folder must live inside a **Shared Drive** and be shared with the service account (the credentials above) because service accounts lack personal storage quota.

3. **(Optional) Install `python-dotenv`** to load environment variables automatically:

   ```bash
   pip install python-dotenv
   ```

4. **Load the `.env` file in your Python entry point**

   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

5. **Run the server**

   ```bash
   uvicorn src.server:app --reload
   ```

6. **Persist the change token**  
   The application saves its sync token to `page_token.txt`, ensuring that history is preserved across restarts.

7. **Disable uploads (if desired)**  
   Set `UPLOAD_ENABLED=false` in `.env` to keep the changelog only on the local filesystem.

## Output format

Each entry in `changelog.jsonl` contains:

- `fileId` and `fileName`
- `eventType` – one of `create`, `update`, or `delete`
- `diff` – textual differences when applicable (empty for create/delete)

---  

*Happy coding! 🎉*  
