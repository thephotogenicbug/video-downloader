import os
import re
import sys
import time
import traceback
import validators
from tqdm import tqdm
import yt_dlp
import instaloader

LINKS_FILE = "pending_downloads.txt"

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename)

def save_pending_links(links):
    with open(LINKS_FILE, 'w') as f:
        for link in links:
            f.write(link + "\n")

def load_pending_links():
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def delete_pending_links_file():
    if os.path.exists(LINKS_FILE):
        os.remove(LINKS_FILE)

def download_video(url, download_path, pending_links):
    def hook(d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0)
            if total > 0:
                if not hasattr(hook, 'pbar'):
                    hook.pbar = tqdm(total=total, unit='B', unit_scale=True, desc="Downloading")
                hook.pbar.update(downloaded - hook.pbar.n)
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
            file_path = os.path.join(download_path, filename)
            
            if os.path.exists(file_path):
                print(f"The file '{filename}' already exists. Skipping download.")
                return
            
            ydl_opts['outtmpl'] = file_path
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if url in pending_links:
                pending_links.remove(url)
                save_pending_links(pending_links)
            
        print(f"Download complete: {filename}")
    except Exception as e:
        if hasattr(hook, 'pbar'):
            hook.pbar.close()
        print(f"An error occurred: {e}")
        traceback.print_exc()

def main():
    print("Content Downloader with Auto-Resume Feature")
    
    pending_links = load_pending_links()
    if pending_links:
        print(f"Resuming {len(pending_links)} pending downloads...")
    
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
            if pending_links:
                for url in pending_links[:]:
                    download_video(url, download_path, pending_links)
                delete_pending_links_file()
                print("All pending downloads completed!")
                continue
            
            mode = input("Choose download mode (single/batch): ").strip().lower()
            if mode == 'single':
                while True:
                    url = input("Enter the URL of the video to download (or type 'exit' to quit): ").strip()
                    if url.lower() == 'exit':
                        print("Exiting the downloader.")
                        break
                    if not validators.url(url):
                        print("Invalid URL. Please enter a valid URL.")
                        continue
                    download_video(url, download_path, pending_links)
            elif mode == 'batch':
                while True:
                    urls = input("Enter URLs of videos to download (separated by commas) or type 'exit' to quit: ").strip()
                    if urls.lower() == 'exit':
                        print("Exiting the downloader.")
                        break
                    urls_list = [url.strip() for url in urls.split(',') if url.strip() and validators.url(url)]
                    if not urls_list:
                        print("No valid URLs provided.")
                        continue
                    
                    pending_links.extend(urls_list)
                    save_pending_links(pending_links)
                    
                    total_links = len(urls_list)
                    print(f"Total URLs to process: {total_links}")
                    for index, url in enumerate(urls_list, start=1):
                        print(f"Processing URL {index}/{total_links}: {url}")
                        download_video(url, download_path, pending_links)
                        print(f"{total_links - index} links remaining.")
                    
                    delete_pending_links_file()
            else:
                print("Invalid mode selected. Please choose 'single' or 'batch'.")
    except KeyboardInterrupt:
        print("\nInput interrupted. Exiting the downloader.")
        save_pending_links(pending_links)

if __name__ == "__main__":
    main()
