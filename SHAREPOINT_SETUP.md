# SharePoint Library Setup Guide

This guide walks you through setting up the SharePoint document libraries with the required columns for Zoom recording metadata.

## Overview

The application uploads files to two separate SharePoint libraries and automatically sets metadata columns for each file:

- **MeetingID** - The Zoom meeting ID
- **Host** - Email address of the meeting host
- **RecordingStart** - Date and time when the recording started

## Step 1: Create Document Libraries

1. Navigate to your SharePoint site
2. Click on **Settings** (gear icon) → **Site contents**
3. Click **+ New** → **Document library**
4. Create the first library:
   - Name: `ZoomVideo`
   - Description: "Zoom video recordings (.mp4 files)"
   - Click **Create**
5. Repeat to create the second library:
   - Name: `ZoomAudio`
   - Description: "Zoom audio recordings and transcripts (.m4a, .vtt files)"
   - Click **Create**

## Step 2: Add Custom Columns to ZoomVideo Library

1. Navigate to the **ZoomVideo** library
2. Click on **Settings** (gear icon) → **Library settings**
3. Under **Columns**, click **Create column**

### Column 1: MeetingID

- **Column name**: `MeetingID`
- **Type**: Single line of text
- **Description**: Zoom meeting ID
- **Require that this column contains information**: No (optional)
- **Maximum number of characters**: 255 (default)
- Click **OK**

### Column 2: Host

- **Column name**: `Host`
- **Type**: Single line of text
- **Description**: Email address of the meeting host
- **Require that this column contains information**: No (optional)
- **Maximum number of characters**: 255 (default)
- Click **OK**

### Column 3: RecordingStart

- **Column name**: `RecordingStart`
- **Type**: Date and Time
- **Description**: Date and time when the recording started
- **Require that this column contains information**: No (optional)
- **Date and Time Format**: Date & Time (important: include time, not just date)
- Click **OK**

## Step 3: Add Custom Columns to ZoomAudio Library

Repeat Step 2 for the **ZoomAudio** library. Create the exact same three columns:
1. **MeetingID** (Single line of text)
2. **Host** (Single line of text)
3. **RecordingStart** (Date and Time)

## Step 4: Verify Column Setup

After creating all columns, verify your setup:

1. Go to **ZoomVideo** library → **Settings** → **Library settings** → **Columns**
   - You should see: MeetingID, Host, RecordingStart (plus default columns like Name, Modified, etc.)

2. Go to **ZoomAudio** library → **Settings** → **Library settings** → **Columns**
   - You should see: MeetingID, Host, RecordingStart (plus default columns)

## Column Internal Names

The application uses these exact column names when setting metadata:
- `MeetingID` (case-sensitive)
- `Host` (case-sensitive)
- `RecordingStart` (case-sensitive)

**Important**: The column names must match exactly. If you use different names (e.g., "Meeting ID" with a space), the metadata updates will fail.

## Alternative: Using Different Column Names

If you need to use different column names in SharePoint (e.g., "Meeting ID" instead of "MeetingID"), you'll need to modify the code in `src/main.py`:

```python
# Find this section around line 245
metadata = {
    "MeetingID": str(meeting_id),      # Change "MeetingID" to your column name
    "Host": host_email,                 # Change "Host" to your column name
    "RecordingStart": recording_start   # Change "RecordingStart" to your column name
}
```

## Creating Views with Metadata

Once columns are set up, you can create custom views to organize recordings:

### View 1: Group by Host

1. In the library, click **All Documents** (view dropdown) → **Create new view**
2. View Name: "By Host"
3. View Type: Standard View
4. Columns to display: Name, Modified, Host, MeetingID, RecordingStart
5. Group By: Host
6. Click **OK**

### View 2: Group by Date

1. Create new view: "By Recording Date"
2. Columns to display: Name, Modified, RecordingStart, Host, MeetingID
3. Group By: RecordingStart (show by month)
4. Sort by: RecordingStart (descending)
5. Click **OK**

### View 3: Search by Meeting ID

1. Create new view: "All Recordings with Metadata"
2. Columns to display: Name, Modified, MeetingID, Host, RecordingStart
3. Filter: Show all items
4. Sort by: RecordingStart (descending)
5. Click **OK**

Now you can use the search box to filter by Meeting ID, Host email, or date.

## Testing Metadata Upload

After running the application, verify that metadata is being set correctly:

1. Navigate to one of the libraries (ZoomVideo or ZoomAudio)
2. Find a recently uploaded file
3. Hover over the file name and click the **...** (more options)
4. Select **Details**
5. In the details pane, you should see:
   - **MeetingID**: The Zoom meeting ID
   - **Host**: The host's email address
   - **RecordingStart**: The date and time the recording started

## Troubleshooting

### Metadata not appearing

**Cause**: Column names don't match exactly
**Solution**:
- Check that column names are exactly `MeetingID`, `Host`, and `RecordingStart` (case-sensitive)
- Check the application logs for errors like "Column not found"

### "Column not found" error

**Cause**: Columns don't exist in the library
**Solution**:
- Verify columns exist in both ZoomVideo and ZoomAudio libraries
- Recreate columns following the exact names above

### Dates not displaying correctly

**Cause**: RecordingStart column is set to "Date Only" instead of "Date & Time"
**Solution**:
- Go to Library Settings → Columns → RecordingStart
- Change "Date and Time Format" to "Date & Time"
- Click **OK**

### Permission errors when setting metadata

**Cause**: Azure AD app doesn't have proper permissions
**Solution**:
- Verify the app has `Sites.ReadWrite.All` permission
- Ensure admin consent was granted
- Try re-granting consent in Azure Portal

## Advanced: PowerShell Script to Create Columns

If you need to set up multiple sites or libraries, use this PowerShell script:

```powershell
# Connect to SharePoint
Connect-PnPOnline -Url "https://yourcompany.sharepoint.com/sites/yoursite" -Interactive

# Function to add columns to a library
function Add-ZoomColumns {
    param($LibraryName)

    # Add MeetingID column
    Add-PnPField -List $LibraryName -DisplayName "MeetingID" -InternalName "MeetingID" -Type Text -AddToDefaultView

    # Add Host column
    Add-PnPField -List $LibraryName -DisplayName "Host" -InternalName "Host" -Type Text -AddToDefaultView

    # Add RecordingStart column
    Add-PnPField -List $LibraryName -DisplayName "RecordingStart" -InternalName "RecordingStart" -Type DateTime -AddToDefaultView
}

# Create libraries and add columns
New-PnPList -Title "ZoomVideo" -Template DocumentLibrary
Add-ZoomColumns -LibraryName "ZoomVideo"

New-PnPList -Title "ZoomAudio" -Template DocumentLibrary
Add-ZoomColumns -LibraryName "ZoomAudio"

Write-Host "Setup complete!"
```

## Next Steps

After setting up the libraries and columns:

1. Test the application with a small date range first
2. Verify metadata is being set correctly
3. Create custom views for your team's needs
4. Set up retention policies if needed
5. Configure permissions for who can access recordings
