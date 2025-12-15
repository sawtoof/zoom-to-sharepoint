# Zoom to SharePoint Recording Transfer

A Python application that automatically downloads Zoom cloud recordings for all members of a Zoom group within a specified date range and uploads them to a SharePoint document library. Handles large files (>100MB) using resumable upload sessions.

## Features

- Downloads recordings for all members of a Zoom group
- Filters recordings by date range
- Supports large file uploads (>100MB) to SharePoint using chunked upload
- Automatically sets SharePoint metadata columns (Meeting ID, Host, Recording Start)
- Organizes recordings by date in separate video and audio libraries
- Progress bars for downloads and uploads
- Download-only mode for local backups
- Cleans up local files after successful upload
- Comprehensive error handling and logging
- Automated scheduling support (cron/Task Scheduler)

## Prerequisites

### Zoom Setup

1. Go to [Zoom Marketplace](https://marketplace.zoom.us/)
2. Click "Develop" → "Build App"
3. Choose "Server-to-Server OAuth" app type
4. Fill in the required information
5. Add the following scopes:
   - `recording:read:admin` - View all user recordings
   - `group:read:admin` - View groups
   - `user:read:admin` - View users
6. Note down:
   - Account ID
   - Client ID
   - Client Secret
7. Get your Group ID:
   - Go to Zoom Admin dashboard → User Management → Groups
   - Click on your group and note the Group ID from the URL

### SharePoint/Azure AD Setup

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
4. Enter a name (e.g., "Zoom to SharePoint Transfer")
5. Under "Supported account types", select "Accounts in this organizational directory only"
6. Click "Register"
7. Note down:
   - Application (client) ID
   - Directory (tenant) ID
8. Create a client secret:
   - Go to "Certificates & secrets" → "New client secret"
   - Add a description and expiration period
   - Copy the secret value (you won't be able to see it again)
9. Configure API permissions:
   - Go to "API permissions" → "Add a permission"
   - Select "Microsoft Graph" → "Application permissions"
   - Add: `Sites.ReadWrite.All`
   - Click "Grant admin consent"

10. Create SharePoint libraries and columns:
   - Go to your SharePoint site
   - Create two document libraries:
     - `ZoomVideo` - for video files (.mp4)
     - `ZoomAudio` - for audio and transcript files (.m4a, .vtt)
   - In **both** libraries, create the following columns (Library Settings → Columns → Create Column):
     - **MeetingID** - Single line of text
     - **Host** - Single line of text
     - **RecordingStart** - Date and Time (include time)

   **See [SHAREPOINT_SETUP.md](SHAREPOINT_SETUP.md) for detailed step-by-step instructions with screenshots and troubleshooting.**

## Installation

1. Clone or download this repository

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file from the example:
```bash
cp .env.example .env
```

6. Edit `.env` and fill in your credentials:
```env
# Zoom Configuration
ZOOM_ACCOUNT_ID=your_zoom_account_id
ZOOM_CLIENT_ID=your_zoom_client_id
ZOOM_CLIENT_SECRET=your_zoom_client_secret
ZOOM_GROUP_ID=your_zoom_group_id

# SharePoint Configuration
SP_TENANT_ID=your_azure_tenant_id
SP_CLIENT_ID=your_azure_app_client_id
SP_CLIENT_SECRET=your_azure_app_client_secret
SP_SITE_URL=https://yourcompany.sharepoint.com/sites/yoursitename
SP_VIDEO_LIBRARY=ZoomVideo
SP_AUDIO_LIBRARY=ZoomAudio

# Optional
DOWNLOAD_DIR=./downloads
```

## Usage

Run the application with a date range:

```bash
cd src
python main.py <from_date> <to_date>
```

### Arguments

- `from_date` (required): Start date in YYYY-MM-DD format
- `to_date` (required): End date in YYYY-MM-DD format
- `--download-dir` (optional): Temporary download directory (default: ./downloads)
- `--download-only` (optional): Only download files without uploading to SharePoint (files will not be deleted)

### Examples

```bash
# Download and upload recordings from January 2024
python main.py 2024-01-01 2024-01-31

# Download and upload recordings for the entire year 2024
python main.py 2024-01-01 2024-12-31

# Specify a custom download directory
python main.py 2024-01-01 2024-12-31 --download-dir ./temp

# Download only (no SharePoint upload, files are kept)
python main.py 2024-01-01 2024-12-31 --download-only

# Download only to a specific directory
python main.py 2024-01-01 2024-12-31 --download-only --download-dir ./recordings

# Show help
python main.py --help
```

### Normal Mode (Default)

The application will:
1. Fetch all members from the specified Zoom group
2. Retrieve recordings for each member within the date range
3. Download each recording to a local temporary directory
4. Upload to SharePoint organized by date and file type
5. Clean up local files after successful upload
6. Display a summary of successful and failed uploads

### Download-Only Mode (`--download-only`)

When using the `--download-only` flag:
1. Fetch all members from the specified Zoom group
2. Retrieve recordings for each member within the date range
3. Download each recording to the specified directory
4. **Files are kept** (not deleted after download)
5. **No SharePoint credentials required**
6. Display a summary of successful and failed downloads

This mode is useful when you want to:
- Create a local backup of recordings
- Download recordings without uploading to SharePoint
- Test the download functionality
- Process files locally before uploading

## Automated Scheduling

You can automate the application to run on a schedule (e.g., download yesterday's recordings every day).

### Ready-to-Use Scripts

The [scripts/](scripts/) directory contains ready-to-use automation scripts:

**Linux/Mac:**
- `scripts/download-yesterday.sh` - Download only (keeps files locally)
- `scripts/upload-yesterday.sh` - Download and upload to SharePoint

**Windows:**
- `scripts/download-yesterday.ps1` - Download only (keeps files locally)
- `scripts/upload-yesterday.ps1` - Download and upload to SharePoint

**Quick Setup:**

```bash
# Linux/Mac
chmod +x scripts/download-yesterday.sh
./scripts/download-yesterday.sh  # Test it

# Add to crontab (runs daily at 2 AM)
echo "0 2 * * * $(pwd)/scripts/download-yesterday.sh" | crontab -

# Windows
.\scripts\download-yesterday.ps1  # Test it
# Then schedule with Task Scheduler (see scripts/README.md)
```

### Advanced Scheduling

See **[SCHEDULING.md](SCHEDULING.md)** for comprehensive documentation on:
- Setting up cron jobs (Linux/Mac) or Task Scheduler (Windows)
- Weekly and monthly scheduling
- Email notifications on success/failure
- Error handling and logging
- Retention policies for old recordings
- Custom date ranges

## File Organization in SharePoint

Files are automatically organized by:
- **Library**: Video files (.mp4) go to `ZoomVideo`, audio/transcript files (.m4a, .vtt) go to `ZoomAudio`
- **Folder structure**: `YYYY/MM - MonthName/YYYY-MM-DD`

Example structure:

```
SharePoint Site
├── ZoomVideo (library for .mp4 files)
│   ├── 2025/
│   │   └── 12 - December/
│   │       └── 2025-12-12/
│   │           ├── 2025-12-12_Team-Standup_shared_screen.mp4
│   │           └── 2025-12-12_Client-Meeting_shared_screen.mp4
│   └── 2024/
│       └── 01 - January/
│           └── 2024-01-15/
│               └── 2024-01-15_Planning-Session_shared_screen.mp4
│
└── ZoomAudio (library for .m4a and .vtt files)
    └── 2025/
        └── 12 - December/
            └── 2025-12-12/
                ├── 2025-12-12_Team-Standup_audio_only.m4a
                └── 2025-12-12_Team-Standup_transcript.vtt
```

## File Naming Convention

Downloaded files are named using the pattern:
```
{meeting_date}_{meeting_topic}_{recording_type}.{extension}
```

Example: `2024-01-15_Team-Standup_shared_screen.mp4`

## Large File Handling

The application automatically handles large files (>100MB):
- Files < 4MB: Simple upload
- Files ≥ 4MB: Chunked resumable upload (10MB chunks)
- Maximum file size: 250GB (SharePoint limit)

## Troubleshooting

### "No recordings found"
- Verify the date range includes dates when recordings were made
- Check that users in the group have cloud recording enabled
- Ensure the Zoom app has the correct scopes

### "Failed to acquire token" (SharePoint)
- Verify Azure AD app credentials are correct
- Ensure admin consent was granted for API permissions
- Check that the client secret hasn't expired

### "Drive not found"
- Verify `SP_VIDEO_LIBRARY` and `SP_AUDIO_LIBRARY` match your SharePoint library names exactly (case-sensitive)
- Default library names: "ZoomVideo", "ZoomAudio"
- You may need to create these libraries in SharePoint before running the application

### "Site not found"
- Verify the `SP_SITE_URL` is correct and accessible
- Format: `https://company.sharepoint.com/sites/sitename`

### Rate limiting
- The application includes a 0.1s delay between user requests
- If you hit rate limits, you can increase this in `zoom_client.py`

## Security Notes

- Never commit the `.env` file to version control
- Store credentials securely
- Regularly rotate client secrets
- Use minimum required API permissions
- Consider using Azure Key Vault for production deployments

## License

MIT License - feel free to use and modify as needed.

## Support

For issues related to:
- Zoom API: [Zoom Developer Forum](https://devforum.zoom.us/)
- Microsoft Graph API: [Microsoft Q&A](https://docs.microsoft.com/en-us/answers/)
