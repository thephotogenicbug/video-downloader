import traceback
import yt_dlp
import re
import os
from tqdm import tqdm
import sys

def sanitize_filename(filename):
    """
    Sanitize the filename to remove any characters that are not allowed in filenames.
    """
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename)

def download_video(url, download_path):
    def hook(d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0)
            if total > 0:
                if not hasattr(hook, 'pbar'):
                    # Initialize the progress bar
                    hook.pbar = tqdm(total=total, unit='B', unit_scale=True, desc="Downloading")
                hook.pbar.update(downloaded - hook.pbar.n)
            else:
                print("Download progress: Unable to determine total size", end='\r')
        elif d['status'] == 'finished':
            if hasattr(hook, 'pbar'):
                hook.pbar.close()
            print("Download complete!")

    ydl_opts = {
        'format': 'bestvideo[height>=1080]+bestaudio/best[height>=1080]/best',  # Attempt to download 1080p or higher
        'noplaylist': True,  # Download only the single video, not playlists
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),  # Output filename template based on the video title and file extension
        'progress_hooks': [hook],
        'quiet': True,  # Suppress the usual download progress output
        'no_warnings': True,  # Suppress warnings
        'logger': None,  # Disable yt-dlp logger to avoid clutter
        'writeinfojson': False,  # Don't create a .info.json file
    }

    try:
        print(f"Processing URL: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = sanitize_filename(info_dict.get('title', 'video'))
            extension = info_dict.get('ext', 'mp4')
            filename = f"{title}.{extension}"
            
            # Set the output filename explicitly
            ydl_opts['outtmpl'] = os.path.join(download_path, filename)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        print(f"Download complete: {filename}")
    except Exception as e:
        if hasattr(hook, 'pbar'):
            hook.pbar.close()
        print(f"An error occurred: {e}")
        traceback.print_exc()

def main():
    print("Video Downloader")

    while True:
        download_path = input("Enter the download path: ").strip()
        if not os.path.isdir(download_path):
            print("Invalid directory path. Please enter a valid path.")
            continue
        else:
            break

    while True:
        url = input("Enter the URL of the video to download (or type 'exit' to quit): ").strip()
        if url.lower() == 'exit':
            print("Exiting the downloader.")
            break
        if not url:
            print("URL cannot be empty.")
            continue

        download_video(url, download_path)

if __name__ == "__main__":
    main()
