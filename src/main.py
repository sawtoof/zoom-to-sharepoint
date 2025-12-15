import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from zoom_client import ZoomClient
from sharepoint_client import SharePointClient


def main():
    """Main application to download Zoom recordings and upload to SharePoint."""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Download Zoom recordings for a group and upload to SharePoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py 2024-01-01 2024-12-31
  python main.py 2024-01-01 2024-01-31 --download-dir ./temp
  python main.py 2024-01-01 2024-12-31 --download-only
        """
    )
    parser.add_argument(
        "from_date",
        help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "to_date",
        help="End date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--download-dir",
        default=None,
        help="Temporary download directory (default: ./downloads)"
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download files without uploading to SharePoint (files will not be deleted)"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Zoom configuration
    zoom_account_id = os.getenv("ZOOM_ACCOUNT_ID")
    zoom_client_id = os.getenv("ZOOM_CLIENT_ID")
    zoom_client_secret = os.getenv("ZOOM_CLIENT_SECRET")
    zoom_group_id = os.getenv("ZOOM_GROUP_ID")

    # SharePoint configuration
    sp_tenant_id = os.getenv("SP_TENANT_ID")
    sp_client_id = os.getenv("SP_CLIENT_ID")
    sp_client_secret = os.getenv("SP_CLIENT_SECRET")
    sp_site_url = os.getenv("SP_SITE_URL")  # e.g., https://contoso.sharepoint.com/sites/sitename
    sp_video_library = os.getenv("SP_VIDEO_LIBRARY", "ZoomVideo")
    sp_audio_library = os.getenv("SP_AUDIO_LIBRARY", "ZoomAudio")

    # Date range from command-line arguments
    from_date = args.from_date
    to_date = args.to_date

    # Temporary download directory
    download_dir = args.download_dir or os.getenv("DOWNLOAD_DIR", "./downloads")

    # Download-only mode flag
    download_only = args.download_only

    # Validate required environment variables
    # SharePoint credentials are only required if not in download-only mode
    required_vars = {
        "ZOOM_ACCOUNT_ID": zoom_account_id,
        "ZOOM_CLIENT_ID": zoom_client_id,
        "ZOOM_CLIENT_SECRET": zoom_client_secret,
        "ZOOM_GROUP_ID": zoom_group_id,
    }

    if not download_only:
        required_vars.update({
            "SP_TENANT_ID": sp_tenant_id,
            "SP_CLIENT_ID": sp_client_id,
            "SP_CLIENT_SECRET": sp_client_secret,
            "SP_SITE_URL": sp_site_url,
        })

    missing_vars = [key for key, value in required_vars.items() if not value]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Validate date format
    try:
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        print("Error: Dates must be in YYYY-MM-DD format")
        parser.print_help()
        sys.exit(1)

    # Create download directory
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    if download_only:
        print("Zoom Recording Download (Download-Only Mode)")
    else:
        print("Zoom to SharePoint Recording Transfer")
    print("=" * 80)
    print(f"Date Range: {from_date} to {to_date}")
    print(f"Download Directory: {download_dir}")
    if download_only:
        print(f"Mode: Download only (files will be kept)")
    else:
        print(f"SharePoint Site: {sp_site_url}")
        print(f"Video Library: {sp_video_library}")
        print(f"Audio Library: {sp_audio_library}")
    print("=" * 80)

    # Initialize clients
    print("\nInitializing Zoom client...")
    zoom = ZoomClient(zoom_account_id, zoom_client_id, zoom_client_secret)

    sharepoint = None
    if not download_only:
        print("Initializing SharePoint client...")
        sharepoint = SharePointClient(
            sp_tenant_id,
            sp_client_id,
            sp_client_secret,
            site_url=sp_site_url
        )

    # Fetch recordings for all group members
    print(f"\nFetching recordings for group {zoom_group_id}...")
    all_recordings = zoom.get_group_recordings(zoom_group_id, from_date, to_date)

    if not all_recordings:
        print("\nNo recordings found for the specified date range.")
        return

    print(f"\nFound recordings for {len(all_recordings)} user(s)")

    # Process recordings for each user
    total_files = 0
    successful_uploads = 0
    failed_uploads = 0

    # Helper function to get month name
    def get_month_name(month_num):
        months = {
            "01": "January", "02": "February", "03": "March", "04": "April",
            "05": "May", "06": "June", "07": "July", "08": "August",
            "09": "September", "10": "October", "11": "November", "12": "December"
        }
        return months.get(month_num, "Unknown")

    # Helper function to create date folder path
    def create_date_folder_path(meeting_date_str):
        """
        Creates folder path in format: YYYY/MM - MonthName/YYYY-MM-DD
        Example: 2025/12 - December/2025-12-12
        """
        year = meeting_date_str[:4]
        month = meeting_date_str[5:7]
        month_name = get_month_name(month)
        return f"{year}/{month} - {month_name}/{meeting_date_str}"

    for user_email, meetings in all_recordings.items():
        print(f"\n{'=' * 80}")
        print(f"Processing recordings for: {user_email}")
        print(f"{'=' * 80}")

        for meeting in meetings:
            meeting_id = meeting.get("id")
            meeting_topic = meeting.get("topic", "Unknown").replace("/", "-").replace("\\", "-")
            meeting_start_time = meeting.get("start_time", "")
            meeting_date = meeting_start_time.split("T")[0]
            host_email = meeting.get("host_email", user_email)  # Use host_email from meeting, fallback to user_email

            print(f"\nMeeting: {meeting_topic} ({meeting_date})")

            recording_files = meeting.get("recording_files", [])

            for rec_file in recording_files:
                total_files += 1

                file_type = rec_file.get("file_type", "")
                file_extension = rec_file.get("file_extension", "mp4")
                recording_type = rec_file.get("recording_type", "")
                download_url = rec_file.get("download_url")
                file_size = rec_file.get("file_size", 0)
                recording_start = rec_file.get("recording_start", meeting_start_time)  # Recording-specific start time

                if not download_url:
                    print(f"  Skipping {recording_type}: No download URL")
                    continue

                # Create filename
                safe_topic = "".join(c for c in meeting_topic if c.isalnum() or c in (' ', '-', '_')).strip()
                filename = f"{meeting_date}_{safe_topic}_{recording_type}.{file_extension}"

                # Download file
                local_path = os.path.join(download_dir, filename)

                print(f"  Downloading {recording_type} ({file_size / (1024*1024):.2f} MB)...")

                if not download_only:
                    # Determine library based on file extension
                    if file_extension.lower() == "mp4":
                        library_name = sp_video_library
                    elif file_extension.lower() in ["m4a", "vtt"]:
                        library_name = sp_audio_library
                    else:
                        # Default to video library for unknown types
                        library_name = sp_video_library

                    # Create date-based folder structure
                    date_folder = create_date_folder_path(meeting_date)
                    print(f"  Target: {library_name}/{date_folder}")

                try:
                    # Get download token
                    access_token = zoom._get_access_token()

                    zoom.download_recording_file(download_url, access_token, local_path)

                    if download_only:
                        # Download-only mode: keep the file
                        successful_uploads += 1
                        print(f"  Successfully downloaded: {filename}")
                    else:
                        # Upload to SharePoint and clean up
                        # Create the date folder structure in SharePoint
                        try:
                            sharepoint.create_folder(date_folder, library_name=library_name)
                        except Exception as folder_error:
                            # Folder might already exist, which is fine
                            pass

                        # Prepare metadata for SharePoint columns
                        metadata = {
                            "MeetingID": str(meeting_id),
                            "Host": host_email,
                            "RecordingStart": recording_start
                        }

                        # Upload to SharePoint
                        print(f"  Uploading to SharePoint...")
                        print(f"  Setting metadata: Meeting ID={meeting_id}, Host={host_email}")
                        sharepoint.upload_file(
                            local_path,
                            date_folder,
                            library_name=library_name,
                            metadata=metadata
                        )

                        # Clean up local file
                        os.remove(local_path)

                        successful_uploads += 1
                        print(f"  Successfully uploaded: {filename}")

                except Exception as e:
                    failed_uploads += 1
                    print(f"  Error processing file: {e}")

                    # Clean up partial download (only if not in download-only mode)
                    if not download_only and os.path.exists(local_path):
                        try:
                            os.remove(local_path)
                        except:
                            pass

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total files processed: {total_files}")
    if download_only:
        print(f"Successful downloads: {successful_uploads}")
        print(f"Failed downloads: {failed_uploads}")
        print(f"Files saved to: {download_dir}")
    else:
        print(f"Successful uploads: {successful_uploads}")
        print(f"Failed uploads: {failed_uploads}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
