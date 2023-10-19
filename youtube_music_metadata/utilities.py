#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilities for interacting with Youtube videos and metadata.
"""

import os
import json
import logging
import requests
import subprocess
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, APIC
from mutagen.oggopus import OggOpus



@contextmanager
def change_dir(destination: Path) -> None:
    """Context manager to temporarily change the working directory."""
    orig_dir = os.getcwd()
    os.chdir(destination)
    try:
        yield
    finally:
        os.chdir(orig_dir)
        
# Get the path to the poetry virtual environment
with change_dir(Path(__file__).parent.parent.resolve().as_posix()):
    POETRY_ENV_PATH = Path(subprocess.getoutput('poetry env info -p').strip())
    YT_DLP_PATH = POETRY_ENV_PATH / "Scripts" / "yt-dlp.exe"


# **********
# Sets up logger
logger = logging.getLogger(__name__)


# **********
def download_audio_with_metadata(url: str, file_path: Optional[Path] = None) -> None:
    """Downloads audio from a Youtube video with embedded metadata using yt-dlp.

    Args:
        url (str): URL of Youtube video.
        file_path (Path, Optional): File path to save audio file to with placeholders for yt-dlp. Defaults to current working directory with filename of video title.

    Raises:
        Exception: If subprocess call fails.
    """
    
    # Prepares file path to save audio file to
    if not file_path:
        file_path = Path.cwd() / "%(title)s.%(ext)s"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepares command to download audio with metadata
    command = [
        YT_DLP_PATH.as_posix(),
        "--embed-thumbnail",
        "--add-metadata",
        "--extract-audio",
        "-o",
        file_path.as_posix(),
        url,
    ]
    
    from pprint import pprint
    pprint(command)
    
    response = subprocess.run(
                    command, 
                    stdout=subprocess.PIPE,
                    shell=False
                )
    
    if not response.returncode == 0:
        raise Exception(f"Subprocess call failed for url {url} when attempting to download video with metadata with code: {response.returncode}")

    
def fetch_metadata(url: str) -> dict:
    """Fetches metadata for a youtube video using Youtube-dl. This metadata is returned as a dict.

    Args:
        url (str): Valid Youtube video URL.

    Returns:
        dict: Dict of video metadata.
    """
    
    metadata = {}
    
    # ****
    command = [
        YT_DLP_PATH.as_posix(),
        "--dump-json",
        url,
    ]
    
    # Gets metadata in json format (in bytes)
    response = subprocess.run(
                        command, 
                        stdout=subprocess.PIPE, 
                        shell=False
                    )
    
    # ****
    # Checks if subprocess call was successful
    if response.returncode == 0:
        try:
            metadata = json.loads(response.stdout)
        except(json.decoder.JSONDecodeError):
            # Most likely fetches metadata for multiple videos (playlist), so this sketchily turns the bytes object to represent a list of dicts.
            metadata = json.loads(b"[" + response.stdout.replace(b"}\n{", b"},{").replace(b"}\n", b"}") + b"]")
        except:
            raise Exception("Failed to load json from stdout of subprocess call for url `%s`" % str(url))
    else:
        raise Exception("Subprocess call failed for url `%s` when attempting to write metadata with code: %i" % (str(url), response.returncode))

    return metadata
    

def download_thumbnail(url: str, file_path: Optional[Path] = None) -> None:
    """Downloads thumbnail from a Youtube video using yt-dlp.

    Args:
        url (str): URL of Youtube video.
        file_path (Optional[Path], optional): File path to save thumbnail to. Defaults to current working directory with filename of video title.

    Raises:
        Exception: If subprocess call fails.
    """
    
    # Prepares file path to save audio file to
    if not file_path:
        file_path = Path.cwd() / "%(title)s.%(ext)s"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    response = subprocess.run(
                        [
                            YT_DLP_PATH.as_posix(),
                            "--write-thumbnail",
                            "--skip-download",
                            "-o",
                            file_path.as_posix(),
                            url,
                        ], shell=False
                    )
    
    if not response.returncode == 0:
        raise Exception(f"Subprocess call failed for url {url} when attempting to download video with metadata with code: {response.returncode}")


def set_cover(cover: str, file_path: Optional[Path] = None) -> None:
    """Sets cover art of file to image.
    Credit to: https://stackoverflow.com/questions/53998371/running-into-problems-setting-cover-art-for-mp4-files-using-python-and-mutagen

    Args:
        url (str): URL of Youtube video.
        file_path (Optional[Path], optional): File path to save file to. Defaults to current working directory with filename of title.
    """
    
    # Prepares file path to save audio file to
    if not file_path:
        file_path = Path.cwd() / "cover.jpg"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    r = requests.get(cover)
    
    cover_path = Path.cwd() / "cover.jpg"
    
    with open(cover_path.as_posix(), 'wb', ) as q:
        q.write(r.content)
        
    if(file_path.as_posix().endswith(".mp3")):
        MP3file = MP3(file_path.as_posix(), ID3=ID3)
        if cover.endswith('.jpg') or cover.endswith('.jpeg'):
            mime = 'image/jpg'
        else:
            mime = 'image/png'
        with open(cover_path.as_posix(), 'rb') as albumart: 
            MP3file.tags.add(APIC(encoding=3, mime=mime, type=3, desc=u'Cover', data=albumart.read()))
        MP3file.save(file_path.as_posix())
    else:
        MP4file = MP4(file_path.as_posix())
        if cover.endswith('.jpg') or cover.endswith('.jpeg'):
            cover_format = 'MP4Cover.FORMAT_JPEG'
        else:
            cover_format = 'MP4Cover.FORMAT_PNG'
        with open(cover_path.as_posix(), 'rb') as f:
            albumart = MP4Cover(f.read(), imageformat=cover_format)
        MP4file.tags['covr'] = [bytes(albumart)]
        MP4file.save(file_path.as_posix())


def set_m4a_metadata(file_path: Path, file_metadata: dict) -> None:
    """Sets audio metadata using Mutagen for m4a files.

    Args:
        file_path (Path): Path to audio file.
        file_metadata (dict): Parsed metadata from Youtube video.
    """
    # Metadata needed to be changed:
    # Title -> Video title          file_metadata["title"]
    # Artist -> Channel Name        file_metadata["channel"]
    # Album -> Custom (Would just use Mp3tag)
    # Year -> 20xx                  file_metadata["upload_date"][0:4]
    # Comment -> URL                file_metadata["webpage_url"]
    # Cover -> Thumbnail          
    
    tags = MP4(file_path.as_posix())
    
    tags["\xa9nam"] = file_metadata["title"]              # Track title
    tags["\xa9ART"] = file_metadata["channel"]            # artist
    tags["\xa9day"] = file_metadata["upload_date"]        # YYYYMMDD
    tags["\xa9cmt"] = file_metadata["webpage_url"]        # URL as comment
    tags["desc"] = file_metadata["description"]           # description
    
    set_cover(file_metadata["thumbnail"], file_path)
    
    tags.save(file_path.as_posix())


def set_opus_metadata(file_path: Path, file_metadata: dict) -> None:
    """Sets audio metadata using Mutagen for opus files.

    Args:
        file_path (Path): Path to audio file.
        file_metadata (dict): Parsed metadata from Youtube video.
    """
    # Metadata mapping might be a bit different for Opus
    tags = OggOpus(file_path.as_posix())

    tags["TITLE"] = file_metadata["title"]
    tags["ARTIST"] = file_metadata["channel"]
    tags["DATE"] = file_metadata["upload_date"]  # Just the year might be enough
    tags["COMMENT"] = file_metadata["webpage_url"]
    tags["DESCRIPTION"] = file_metadata["description"]
    
    # set_cover function would need adjustments for .opus files as well
    
    tags.save()



def load_logging_config(config_path: Path) -> dict:
    """Attempts to load logging config from JSON file.

    Args:
        config_path (Path): Path to logging config JSON file.

    Raises:
        ValueError: If invalid JSON in logging config.

    Returns:
        dict: Logging config.
    """
    try:
        return json.loads(config_path.read_text())
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in logging config: {config_path}")



# **********
if __name__ == "__main__":
    pass
