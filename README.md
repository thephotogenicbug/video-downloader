# Video Downloader using python

This is a Python script for downloading videos from various sources using `yt-dlp`. The script provides a command-line interface for users to specify the video URL and the download path.

## Features

- Downloads videos in 1080p or higher quality.
- Displays a progress bar during the download.
- Sanitizes filenames to remove illegal characters.
- Generates a `requirements.txt` file listing the dependencies.

## Requirements

- Python 3.x
- `yt-dlp`
- `tqdm`

## Installation

1. Clone the repository or download the script.

    ```bash
    git clone https://github.com/thephotogenicbug/python-video-downloader.git
    cd python-video-downloader
    ```

2. Install the required packages.

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Run the script.

    ```bash
    python video-downloader.py
    ```

2. Enter the download path when prompted.
3. Enter the video URL when prompted.

## Example

```bash
python video-downloader.py
Enter the download path: /path/to/download
Enter the URL of the video to download (or type 'exit' to quit): https://www.youtube.com/watch?v=dQw4w9WgXcQ
