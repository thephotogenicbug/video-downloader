import os
import re
import sys
import time
import traceback
import validators
from tqdm import tqdm
import yt_dlp
import instaloader

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

def download_instagram_content(url, download_path, username=None, password=None):
    session_file = "instaloader_session"

    loader = instaloader.Instaloader(
        dirname_pattern=download_path,
        filename_pattern='{shortcode}',
        post_metadata_txt_pattern=None,
        download_video_thumbnails=False,
        compress_json=False
    )

    def login():
        try:
            loader.load_session_from_file(username, session_file)
            print("Session loaded successfully.")
        except FileNotFoundError:
            print("Session file not found. Logging in.")
            if not username or not password:
                raise ValueError("Username and password are required for the first login.")
            loader.context.log("Logging in...")
            loader.login(username, password)
            loader.save_session_to_file(session_file)

    def retry_request(shortcode, max_retries=5, backoff_factor=2):
        attempt = 0
        while attempt < max_retries:
            try:
                post = instaloader.Post.from_shortcode(loader.context, shortcode)
                return post
            except instaloader.exceptions.ConnectionException as e:
                if 'Please wait a few minutes before you try again' in str(e):
                    attempt += 1
                    wait_time = backoff_factor ** attempt
                    print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise
        raise RuntimeError(f"Failed to fetch post after {max_retries} retries.")

    try:
        login()

        # Extract shortcode from the URL
        shortcode = url.split("/")[-2]
        post = retry_request(shortcode)
        print(f"Downloading content from: {url}")

        if post.is_video:
            filename = f"{sanitize_filename(post.shortcode)}.mp4"
        else:
            filename = f"{sanitize_filename(post.shortcode)}.jpg"

        file_path = os.path.join(download_path, filename)
        if os.path.exists(file_path):
            print(f"The file '{filename}' already exists. Skipping download.")
        else:
            print(f"Downloading: {filename}")
            loader.download_post(post, target=download_path)
            print(f"Download complete: {filename}")

    except instaloader.exceptions.BadCredentialsException:
        print("Invalid login credentials. Please check your username and password.")
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

def create_requirements():
    if os.path.exists('requirements.txt'):
        print("requirements.txt already exists. Skipping creation.")
        return

    requirements = ["yt-dlp", "tqdm", "validators", "instaloader"]
    with open('requirements.txt', 'w') as f:
        for requirement in requirements:
            f.write(f"{requirement}\n")
    print("requirements.txt file created successfully.")

def main():
    print("Content Downloader")

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
            mode = input("Choose download mode (single/batch/instagram): ").strip().lower()
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
            elif mode == 'instagram':
                try:
                    username = input("Enter your Instagram username: ").strip()
                    password = input("Enter your Instagram password: ").strip()
                except KeyboardInterrupt:
                    print("\nInput interrupted. Exiting the downloader.")
                    return

                while True:
                    url = input("Enter the Instagram post URL (or type 'exit' to quit): ").strip()
                    if url.lower() == 'exit':
                        print("Exiting the downloader.")
                        break
                    if not url:
                        print("URL cannot be empty.")
                        continue
                    if 'instagram.com' not in url:
                        print("Invalid Instagram URL. Please enter a valid Instagram post URL.")
                        continue

                    download_instagram_content(url, download_path, username, password)
            else:
                print("Invalid mode selected. Please choose 'single', 'batch', or 'instagram'.")
    except KeyboardInterrupt:
        print("\nInput interrupted. Exiting the downloader.")

if __name__ == "__main__":
    main()
