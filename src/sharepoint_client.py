import requests
import msal
import os
from typing import Optional
from tqdm import tqdm


class SharePointClient:
    """Client for uploading files to SharePoint using Microsoft Graph API."""

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        site_id: Optional[str] = None,
        site_url: Optional[str] = None
    ):
        """
        Initialize SharePoint client.

        Args:
            tenant_id: Azure AD Tenant ID
            client_id: Azure AD Application (client) ID
            client_secret: Azure AD Client Secret
            site_id: SharePoint Site ID (optional if site_url provided)
            site_url: SharePoint Site URL (optional if site_id provided)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.site_id = site_id
        self.site_url = site_url
        self.access_token = None
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"

    def _get_access_token(self) -> str:
        """
        Get access token using MSAL client credentials flow.

        Returns:
            Access token string
        """
        if self.access_token:
            return self.access_token

        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        scopes = ["https://graph.microsoft.com/.default"]

        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret
        )

        result = app.acquire_token_silent(scopes, account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=scopes)

        if "access_token" in result:
            self.access_token = result["access_token"]
            return self.access_token
        else:
            raise Exception(f"Failed to acquire token: {result.get('error_description')}")

    def _get_site_id(self) -> str:
        """
        Get site ID from site URL if not already provided.

        Returns:
            Site ID
        """
        if self.site_id:
            return self.site_id

        if not self.site_url:
            raise ValueError("Either site_id or site_url must be provided")

        # Parse site URL
        # Format: https://contoso.sharepoint.com/sites/sitename
        parts = self.site_url.replace("https://", "").split("/")
        hostname = parts[0]
        site_path = "/" + "/".join(parts[1:]) if len(parts) > 1 else ""

        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.graph_endpoint}/sites/{hostname}:{site_path}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        self.site_id = response.json()["id"]
        return self.site_id

    def _create_upload_session(
        self,
        drive_id: str,
        folder_path: str,
        file_name: str
    ) -> dict:
        """
        Create an upload session for large files.

        Args:
            drive_id: SharePoint drive ID
            folder_path: Folder path in SharePoint
            file_name: Name of the file

        Returns:
            Upload session details
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Construct the item path
        item_path = f"{folder_path}/{file_name}".replace("//", "/")
        if not item_path.startswith("/"):
            item_path = "/" + item_path

        url = f"{self.graph_endpoint}/drives/{drive_id}/root:{item_path}:/createUploadSession"

        body = {
            "item": {
                "@microsoft.graph.conflictBehavior": "rename",
                "name": file_name
            }
        }

        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        return response.json()

    def upload_file(
        self,
        file_path: str,
        folder_path: str,
        drive_id: Optional[str] = None,
        library_name: str = "Documents",
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Upload a file to SharePoint. Handles both small and large files.

        Args:
            file_path: Local path to file
            folder_path: Destination folder path in SharePoint (relative to library)
            drive_id: Drive ID (optional, will use default document library if not provided)
            library_name: Name of document library (default: "Documents")
            metadata: Optional metadata dictionary to set on the file
                     Example: {"MeetingID": "123", "Host": "user@example.com", "RecordingStart": "2024-01-15T10:30:00Z"}

        Returns:
            Upload result metadata
        """
        site_id = self._get_site_id()

        # Get drive ID if not provided
        if not drive_id:
            drive_id = self._get_drive_id(site_id, library_name)

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        # Use simple upload for files < 4MB, resumable upload for larger files
        if file_size < 4 * 1024 * 1024:
            result = self._upload_small_file(drive_id, folder_path, file_path, file_name)
        else:
            result = self._upload_large_file(drive_id, folder_path, file_path, file_name, file_size)

        # Update metadata if provided
        if metadata and result.get("id"):
            self._update_file_metadata(drive_id, result["id"], metadata)

        return result

    def _get_drive_id(self, site_id: str, library_name: str) -> str:
        """
        Get the drive ID for a document library.

        Args:
            site_id: SharePoint site ID
            library_name: Name of the document library

        Returns:
            Drive ID
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.graph_endpoint}/sites/{site_id}/drives"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        drives = response.json()["value"]
        for drive in drives:
            if drive["name"] == library_name:
                return drive["id"]

        raise ValueError(f"Drive '{library_name}' not found")

    def _upload_small_file(
        self,
        drive_id: str,
        folder_path: str,
        file_path: str,
        file_name: str
    ) -> dict:
        """
        Upload a small file (< 4MB) using simple upload.

        Args:
            drive_id: SharePoint drive ID
            folder_path: Folder path in SharePoint
            file_path: Local file path
            file_name: File name

        Returns:
            Upload result
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }

        item_path = f"{folder_path}/{file_name}".replace("//", "/")
        if not item_path.startswith("/"):
            item_path = "/" + item_path

        url = f"{self.graph_endpoint}/drives/{drive_id}/root:{item_path}:/content"

        with open(file_path, "rb") as f:
            file_content = f.read()

        response = requests.put(url, headers=headers, data=file_content)
        response.raise_for_status()

        return response.json()

    def _upload_large_file(
        self,
        drive_id: str,
        folder_path: str,
        file_path: str,
        file_name: str,
        file_size: int
    ) -> dict:
        """
        Upload a large file using resumable upload session.
        Required for files > 4MB, supports up to 250GB.

        Args:
            drive_id: SharePoint drive ID
            folder_path: Folder path in SharePoint
            file_path: Local file path
            file_name: File name
            file_size: Size of file in bytes

        Returns:
            Upload result
        """
        # Create upload session
        session = self._create_upload_session(drive_id, folder_path, file_name)
        upload_url = session["uploadUrl"]

        # Upload in chunks (10MB chunks recommended by Microsoft)
        chunk_size = 10 * 1024 * 1024  # 10MB
        uploaded_bytes = 0

        with open(file_path, "rb") as f:
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Uploading {file_name}") as pbar:
                while uploaded_bytes < file_size:
                    chunk_start = uploaded_bytes
                    chunk_end = min(uploaded_bytes + chunk_size, file_size)
                    chunk_data = f.read(chunk_end - chunk_start)

                    headers = {
                        "Content-Length": str(len(chunk_data)),
                        "Content-Range": f"bytes {chunk_start}-{chunk_end - 1}/{file_size}"
                    }

                    response = requests.put(upload_url, headers=headers, data=chunk_data)

                    if response.status_code not in [200, 201, 202]:
                        response.raise_for_status()

                    uploaded_bytes = chunk_end
                    pbar.update(len(chunk_data))

        # Final response contains the file metadata
        return response.json()

    def create_folder(
        self,
        folder_path: str,
        drive_id: Optional[str] = None,
        library_name: str = "Documents"
    ) -> dict:
        """
        Create a folder in SharePoint, including nested folders if needed.
        Creates parent folders recursively if they don't exist.

        Args:
            folder_path: Path of folder to create (e.g., "2025/12 - December/2025-12-12")
            drive_id: Drive ID (optional)
            library_name: Name of document library

        Returns:
            Folder metadata
        """
        site_id = self._get_site_id()

        if not drive_id:
            drive_id = self._get_drive_id(site_id, library_name)

        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Split path into parts and create each level
        parts = folder_path.strip("/").split("/")

        # Create folders level by level
        current_path = ""
        for i, part in enumerate(parts):
            if current_path:
                parent_path = current_path
                url = f"{self.graph_endpoint}/drives/{drive_id}/root:/{parent_path}:/children"
            else:
                url = f"{self.graph_endpoint}/drives/{drive_id}/root/children"

            body = {
                "name": part,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "fail"
            }

            response = requests.post(url, headers=headers, json=body)

            # 409 means folder already exists, which is fine - continue to next level
            if response.status_code == 409:
                # Folder exists, continue
                pass
            elif response.status_code not in [200, 201]:
                response.raise_for_status()

            # Update current path for next iteration
            current_path = f"{current_path}/{part}" if current_path else part

        return {"status": "created", "path": folder_path}

    def _update_file_metadata(
        self,
        drive_id: str,
        item_id: str,
        metadata: dict
    ) -> dict:
        """
        Update metadata (list item fields) for an uploaded file.

        Args:
            drive_id: SharePoint drive ID
            item_id: ID of the uploaded file/item
            metadata: Dictionary of field names and values to update

        Returns:
            Updated item metadata
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Use the listItem endpoint to update SharePoint list columns
        url = f"{self.graph_endpoint}/drives/{drive_id}/items/{item_id}/listItem/fields"

        response = requests.patch(url, headers=headers, json=metadata)
        response.raise_for_status()

        return response.json()
