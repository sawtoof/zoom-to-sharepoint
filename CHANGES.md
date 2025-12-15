# Changes Summary

## Updated File Organization Structure

The application has been updated to organize recordings by date and file type instead of by user.

### Key Changes

#### 1. Separate Libraries for Different File Types
- **MP4 files** (.mp4) → `ZoomVideo` library
- **Audio/Transcript files** (.m4a, .vtt) → `ZoomAudio` library

#### 2. Date-Based Folder Structure
Files are now organized in a hierarchical date structure:
```
YYYY/MM - MonthName/YYYY-MM-DD
```

Example:
```
2025/12 - December/2025-12-12
```

#### 3. Complete Folder Structure Example

**ZoomVideo Library:**
```
ZoomVideo/
├── 2025/
│   └── 12 - December/
│       └── 2025-12-12/
│           ├── 2025-12-12_Team-Standup_shared_screen.mp4
│           └── 2025-12-12_Client-Meeting_shared_screen.mp4
└── 2024/
    └── 01 - January/
        └── 2024-01-15/
            └── 2024-01-15_Planning-Session_shared_screen.mp4
```

**ZoomAudio Library:**
```
ZoomAudio/
└── 2025/
    └── 12 - December/
        └── 2025-12-12/
            ├── 2025-12-12_Team-Standup_audio_only.m4a
            └── 2025-12-12_Team-Standup_transcript.vtt
```

### Configuration Changes

#### Environment Variables (.env file)
**Before:**
```env
SP_LIBRARY_NAME=Documents
SP_FOLDER_PATH=ZoomRecordings
```

**After:**
```env
SP_VIDEO_LIBRARY=ZoomVideo
SP_AUDIO_LIBRARY=ZoomAudio
```

### Code Changes

#### Files Modified:
1. **src/main.py**
   - Removed user-specific folder organization
   - Added file type detection (mp4 vs m4a/vtt)
   - Added date-based folder path creation
   - Updated to use separate libraries for video and audio files
   - Added helper functions: `get_month_name()` and `create_date_folder_path()`

2. **src/sharepoint_client.py**
   - Updated `create_folder()` method to support nested folder creation
   - Automatically creates parent folders if they don't exist
   - Now creates folders level by level: Year → Month → Date

3. **.env.example**
   - Replaced `SP_LIBRARY_NAME` and `SP_FOLDER_PATH` with `SP_VIDEO_LIBRARY` and `SP_AUDIO_LIBRARY`

4. **README.md**
   - Updated file organization documentation
   - Updated configuration examples
   - Updated troubleshooting section

### Migration Notes

If you have an existing `.env` file, you need to update it:

1. Remove these lines:
   ```env
   SP_LIBRARY_NAME=Documents
   SP_FOLDER_PATH=ZoomRecordings
   ```

2. Add these lines:
   ```env
   SP_VIDEO_LIBRARY=ZoomVideo
   SP_AUDIO_LIBRARY=ZoomAudio
   ```

3. Create the `ZoomVideo` and `ZoomAudio` libraries in your SharePoint site before running the application.

### Benefits of New Structure

1. **Better Organization**: Files are grouped by date, making it easier to find recordings from specific time periods
2. **Separation by Type**: Video and audio files are in separate libraries for easier management
3. **Scalability**: Hierarchical folder structure (Year/Month/Date) scales better with large numbers of recordings
4. **Chronological Browsing**: Easy to navigate through recordings chronologically

## New Feature: Download-Only Mode

### Overview
A new `--download-only` command-line flag has been added that allows you to download Zoom recordings without uploading to SharePoint.

### Usage
```bash
python main.py 2024-01-01 2024-12-31 --download-only
```

### Features
- **No SharePoint credentials required**: When using `--download-only`, you don't need to configure SharePoint settings
- **Files are kept**: Downloaded files remain in the download directory and are not deleted
- **Useful for**:
  - Creating local backups of recordings
  - Testing download functionality
  - Processing files locally before uploading
  - Archiving recordings to external storage

### Examples
```bash
# Download only (uses default ./downloads directory)
python main.py 2024-01-01 2024-12-31 --download-only

# Download to a specific directory
python main.py 2024-01-01 2024-12-31 --download-only --download-dir ./my-recordings

# Download only for a specific date range
python main.py 2024-12-01 2024-12-15 --download-only
```

### Environment Variables Required
When using `--download-only`, you only need Zoom credentials:
```env
ZOOM_ACCOUNT_ID=your_zoom_account_id
ZOOM_CLIENT_ID=your_zoom_client_id
ZOOM_CLIENT_SECRET=your_zoom_client_secret
ZOOM_GROUP_ID=your_zoom_group_id
```

SharePoint credentials (SP_*) are not required in download-only mode.

## New Feature: Automatic Metadata Population

### Overview
The application now automatically sets SharePoint metadata columns when uploading files. Each uploaded file will have the following metadata populated:

- **MeetingID** - The Zoom meeting ID
- **Host** - Email address of the meeting host
- **RecordingStart** - Date and time when the recording started

### SharePoint Setup Required

You must create custom columns in your SharePoint libraries before using this feature:

1. In both `ZoomVideo` and `ZoomAudio` libraries, create these columns:
   - **MeetingID** - Single line of text
   - **Host** - Single line of text
   - **RecordingStart** - Date and Time (include time)

2. Column names must match exactly (case-sensitive)

See **[SHAREPOINT_SETUP.md](SHAREPOINT_SETUP.md)** for detailed setup instructions.

### Benefits

- **Easy Searching**: Search recordings by meeting ID or host email
- **Better Organization**: Create views grouped by host or date
- **Audit Trail**: Know exactly when each recording was created
- **Integration**: Use metadata in Power Automate flows or other integrations

### Technical Details

The metadata is set automatically during the upload process using the Microsoft Graph API's `listItem/fields` endpoint. The metadata comes directly from Zoom's API response for each recording.

**Code location**: [src/main.py](src/main.py) (lines 244-259) and [src/sharepoint_client.py](src/sharepoint_client.py) (lines 363-392)
