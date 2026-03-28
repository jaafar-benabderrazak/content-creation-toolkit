"""Interactive YouTube API credential setup wizard.

Walks through:
1. Google Cloud Project creation guidance
2. YouTube Data API v3 enabling
3. OAuth 2.0 client ID setup
4. client_secrets.json placement
5. OAuth consent flow (opens browser)
6. Token persistence verification

Run: python setup_youtube.py
"""
from __future__ import annotations

import json
import sys
import webbrowser
from pathlib import Path

CREDENTIALS_DIR = Path("credentials")
CLIENT_SECRETS = CREDENTIALS_DIR / "client_secrets.json"
TOKEN_FILE = CREDENTIALS_DIR / "youtube_token.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def step(n: int, title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  Step {n}: {title}")
    print(f"{'='*60}\n")


def main():
    print("\n" + "="*60)
    print("  YouTube API Credential Setup Wizard")
    print("="*60)

    # ----------------------------------------------------------------
    # Step 1: Google Cloud Project
    # ----------------------------------------------------------------
    step(1, "Google Cloud Project")
    print("You need a Google Cloud project with YouTube Data API v3 enabled.")
    print()
    print("  1. Go to: https://console.cloud.google.com/")
    print("  2. Create a new project (or select existing)")
    print("  3. Note the project name")
    print()
    input("Press Enter when your project is ready...")

    # ----------------------------------------------------------------
    # Step 2: Enable YouTube Data API v3
    # ----------------------------------------------------------------
    step(2, "Enable YouTube Data API v3")
    url = "https://console.cloud.google.com/apis/library/youtube.googleapis.com"
    print(f"  Opening: {url}")
    print()
    print("  Click 'ENABLE' on that page.")
    print()
    webbrowser.open(url)
    input("Press Enter when YouTube Data API v3 is enabled...")

    # ----------------------------------------------------------------
    # Step 3: OAuth Consent Screen
    # ----------------------------------------------------------------
    step(3, "Configure OAuth Consent Screen")
    url2 = "https://console.cloud.google.com/apis/credentials/consent"
    print(f"  Opening: {url2}")
    print()
    print("  1. Select 'External' user type → Create")
    print("  2. Fill in App name (e.g., 'Content Creation Toolkit')")
    print("  3. Add your email as support email")
    print("  4. Add scopes: youtube.upload")
    print("  5. Add yourself as test user")
    print("  6. Save")
    print()
    print("  IMPORTANT: For tokens lasting >7 days, publish the app")
    print("  (go to 'Publishing status' → 'Publish App')")
    print()
    webbrowser.open(url2)
    input("Press Enter when consent screen is configured...")

    # ----------------------------------------------------------------
    # Step 4: Create OAuth Client ID
    # ----------------------------------------------------------------
    step(4, "Create OAuth 2.0 Client ID")
    url3 = "https://console.cloud.google.com/apis/credentials"
    print(f"  Opening: {url3}")
    print()
    print("  1. Click '+ CREATE CREDENTIALS' → 'OAuth client ID'")
    print("  2. Application type: 'Desktop app'")
    print("  3. Name: 'Content Creation Toolkit'")
    print("  4. Click 'CREATE'")
    print("  5. Click 'DOWNLOAD JSON' on the popup")
    print(f"  6. Save the file as: {CLIENT_SECRETS.absolute()}")
    print()
    webbrowser.open(url3)

    CREDENTIALS_DIR.mkdir(exist_ok=True)

    while not CLIENT_SECRETS.exists():
        input(f"\nWaiting for {CLIENT_SECRETS}... (Press Enter to re-check)")

    # Validate it's real JSON
    try:
        data = json.loads(CLIENT_SECRETS.read_text())
        if "installed" in data or "web" in data:
            print(f"\n  client_secrets.json found and valid!")
        else:
            print(f"\n  WARNING: File exists but may not be a valid OAuth client JSON")
    except json.JSONDecodeError:
        print(f"\n  ERROR: {CLIENT_SECRETS} is not valid JSON")
        sys.exit(1)

    # ----------------------------------------------------------------
    # Step 5: OAuth Consent Flow
    # ----------------------------------------------------------------
    step(5, "Authorize with Google (Browser)")
    print("  Opening browser for Google OAuth consent...")
    print("  Sign in and allow access to YouTube uploads.")
    print()

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS), SCOPES
        )
        creds = flow.run_local_server(port=0)

        # Save token
        TOKEN_FILE.write_text(creds.to_json())
        print(f"\n  Token saved to: {TOKEN_FILE}")

    except ImportError:
        print("\n  ERROR: Missing packages. Run:")
        print("    pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
        sys.exit(1)

    # ----------------------------------------------------------------
    # Step 6: Verify
    # ----------------------------------------------------------------
    step(6, "Verification")
    try:
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("youtube", "v3", credentials=creds)
        channels = service.channels().list(part="snippet", mine=True).execute()

        if channels.get("items"):
            channel = channels["items"][0]["snippet"]
            print(f"  Connected to: {channel['title']}")
            print(f"  Channel ID: {channels['items'][0]['id']}")
        else:
            print("  WARNING: No YouTube channel found for this account")
            print("  You may need to create a YouTube channel first")

    except Exception as e:
        print(f"  Verification failed: {e}")
        print("  Token was saved — you can try publishing anyway")

    # ----------------------------------------------------------------
    # Done
    # ----------------------------------------------------------------
    print("\n" + "="*60)
    print("  Setup Complete!")
    print("="*60)
    print()
    print("  Files created:")
    print(f"    {CLIENT_SECRETS}")
    print(f"    {TOKEN_FILE}")
    print()
    print("  YouTube publishing is now active.")
    print("  Set 'youtube_enabled: true' in your profile YAML.")
    print()
    print("  Test upload:")
    print("    python shared/publisher.py --check-quota")
    print()


if __name__ == "__main__":
    main()
