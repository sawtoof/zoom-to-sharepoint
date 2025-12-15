import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import base64
import jwt


class ZoomClient:
    """Client for interacting with Zoom API to retrieve recordings."""

    def __init__(self, account_id: str, client_id: str, client_secret: str):
        """
        Initialize Zoom client with Server-to-Server OAuth credentials.

        Args:
            account_id: Zoom Account ID
            client_id: Zoom Client ID
            client_secret: Zoom Client Secret
        """
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
        self.base_url = "https://api.zoom.us/v2"

    def _get_access_token(self) -> str:
        """
        Get OAuth access token using Server-to-Server OAuth.

        Returns:
            Access token string
        """
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        token_url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={self.account_id}"

        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(token_url, headers=headers)
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]
        # Set expiry with 5 minute buffer
        self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 300)

        return self.access_token

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make authenticated request to Zoom API.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    def get_group_members(self, group_id: str) -> List[Dict]:
        """
        Get all members of a Zoom group.

        Args:
            group_id: Zoom group ID

        Returns:
            List of user dictionaries
        """
        members = []
        page_size = 300
        next_page_token = None

        while True:
            params = {"page_size": page_size}
            if next_page_token:
                params["next_page_token"] = next_page_token

            data = self._make_request(f"groups/{group_id}/members", params)
            members.extend(data.get("members", []))

            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break

        return members

    def get_user_recordings(
        self,
        user_id: str,
        from_date: str,
        to_date: str
    ) -> List[Dict]:
        """
        Get recordings for a specific user within a date range.

        Args:
            user_id: Zoom user ID or email
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of recording dictionaries
        """
        recordings = []
        page_size = 300
        next_page_token = None

        params = {
            "from": from_date,
            "to": to_date,
            "page_size": page_size
        }

        while True:
            if next_page_token:
                params["next_page_token"] = next_page_token

            try:
                data = self._make_request(f"users/{user_id}/recordings", params)
                meetings = data.get("meetings", [])
                recordings.extend(meetings)

                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # User might not have recordings
                    break
                raise

        return recordings

    def get_group_recordings(
        self,
        group_id: str,
        from_date: str,
        to_date: str
    ) -> Dict[str, List[Dict]]:
        """
        Get recordings for all members of a group within a date range.

        Args:
            group_id: Zoom group ID
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary mapping user emails to their recordings
        """
        members = self.get_group_members(group_id)
        all_recordings = {}

        print(f"Found {len(members)} members in group")

        for member in members:
            user_id = member.get("id")
            user_email = member.get("email")

            print(f"Fetching recordings for {user_email}...")

            try:
                recordings = self.get_user_recordings(user_id, from_date, to_date)
                if recordings:
                    all_recordings[user_email] = recordings
                    print(f"  Found {len(recordings)} recording(s)")
                else:
                    print(f"  No recordings found")

                # Rate limiting - be nice to the API
                time.sleep(0.1)

            except Exception as e:
                print(f"  Error fetching recordings: {e}")
                continue

        return all_recordings

    def download_recording_file(
        self,
        download_url: str,
        download_token: str,
        output_path: str
    ) -> None:
        """
        Download a recording file.

        Args:
            download_url: URL to download from
            download_token: Access token for download
            output_path: Local path to save file
        """
        headers = {
            "Authorization": f"Bearer {download_token}"
        }

        response = requests.get(download_url, headers=headers, stream=True)
        response.raise_for_status()

        # Get total file size
        total_size = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                from tqdm import tqdm
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=output_path.split('\\')[-1]) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
