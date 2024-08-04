import yt_dlp
import re
import os
from tqdm import tqdm
import sys
import traceback
import validators

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename)

def download_video(url, download_path):
    def hook(d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0)
            if total > 0:
                if not hasattr(hook, 'pbar'):
                    hook.pbar = tqdm(total=total, unit='B', unit_scale=True, desc="Downloading")
                hook.pbar.update(downloaded - hook.pbar.n)
            else:
                print("Download progress: Unable to determine total size", end='\r')
        elif d['status'] == 'finished':
            if hasattr(hook, 'pbar'):
                hook.pbar.close()
            print("Download complete!")

    ydl_opts = {
        'format': 'bestvideo[height>=1080]+bestaudio/best[height>=1080]/best',
        'noplaylist': True,
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'progress_hooks': [hook],
        'quiet': True,
        'no_warnings': True,
        'logger': None,
        'writeinfojson': False
    }

    try:
        print(f"Processing URL: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = sanitize_filename(info_dict.get('title', 'video'))
            extension = info_dict.get('ext', 'mp4')
            filename = f"{title}.{extension}"
            
            # Check if the file already exists
            file_path = os.path.join(download_path, filename)
            if os.path.exists(file_path):
                print(f"The file '{filename}' already exists. Skipping download.")
                return

            ydl_opts['outtmpl'] = file_path
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        print(f"Download complete: {filename}")
    except Exception as e:
        if hasattr(hook, 'pbar'):
            hook.pbar.close()
        print(f"An error occurred: {e}")
        traceback.print_exc()

def create_requirements():
    if os.path.exists('requirements.txt'):
        print("requirements.txt already exists. Skipping creation.")
        return

    requirements = ["yt-dlp", "tqdm", "validators"]
    with open('requirements.txt', 'w') as f:
        for requirement in requirements:
            f.write(f"{requirement}\n")
    print("requirements.txt file created successfully.")

def main():
    print("Video Downloader")

    create_requirements()

    try:
        while True:
            download_path = input("Enter the download path: ").strip()
            if not os.path.isdir(download_path):
                print("Invalid directory path. Please enter a valid path.")
                continue
            else:
                break
    except KeyboardInterrupt:
        print("\nDownload path input interrupted. Exiting the downloader.")
        return

    try:
        while True:
            mode = input("Choose download mode (single/batch): ").strip().lower()
            if mode == 'single':
                while True:
                    url = input("Enter the URL of the video to download (or type 'exit' to quit): ").strip()
                    if url.lower() == 'exit':
                        print("Exiting the downloader.")
                        break
                    if not url:
                        print("URL cannot be empty.")
                        continue
                    if not validators.url(url):
                        print("Invalid URL. Please enter a valid URL.")
                        continue

                    download_video(url, download_path)
            elif mode == 'batch':
                while True:
                    urls = input("Enter URLs of videos to download (separated by commas) or type 'exit' to quit: ").strip()
                    if urls.lower() == 'exit':
                        print("Exiting the downloader.")
                        break
                    urls_list = [url.strip() for url in urls.split(',') if url.strip()]
                    if not urls_list:
                        print("No valid URLs provided.")
                        continue
                    for url in urls_list:
                        if not validators.url(url):
                            print(f"Invalid URL: {url}. Skipping.")
                            continue
                        download_video(url, download_path)
            else:
                print("Invalid mode selected. Please choose 'single' or 'batch'.")
    except KeyboardInterrupt:
        print("\nInput interrupted. Exiting the downloader.")

if __name__ == "__main__":
    main()
