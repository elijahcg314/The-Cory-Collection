import os
import json
import yt_dlp
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"

def get_authenticated_service():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=8080)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)

def download_videos(channel_url):
    ydl_opts = {
        "outtmpl": "%(title).200s.%(ext)s",
        "writedescription": True,
        "writeinfojson": True,
        "writeannotations": True,
        "writeallthumbnails": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitlesformat": "srt",
        "embedsubtitles": True,
        "merge_output_format": "mp4",
        "format": "bestvideo+bestaudio",
        "quiet": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([channel_url])

def upload_video(youtube, video_file, info_file):
    with open(info_file, 'r', encoding='utf-8') as f:
        info = json.load(f)

    request_body = {
        "snippet": {
            "title": info["title"],
            "description": info.get("description", ""),
            "tags": info.get("tags", []),
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype="video/*")
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print("Upload complete:", response["id"])

def main():
    # Step 1: Download
    channel_url = "https://www.youtube.com/channel/UCiYcA0gJzg855iSKMrX3oHg"
    print("Downloading videos...")
    download_videos(channel_url)

    # Step 2: Authenticate Upload Channel
    print("Authenticating upload account...")
    youtube = get_authenticated_service()

    # Step 3: Upload
    for file in os.listdir("."):
        if file.endswith(".mp4"):
            base = file[:-4]
            info_file = base + ".info.json"
            if os.path.exists(info_file):
                print(f"Uploading {file}...")
                upload_video(youtube, file, info_file)

if __name__ == "__main__":
    main()
