#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__main__.py
~~~~~~~~~~~~~~~~~~

Remember to always check logs after program runs as errors and warnings will be recorded there.

Places that can be changed:
- The main() program ofc (recommended). Comment/uncomment sections what you want to run.

Feel free to change whatever else as long as you know what you're doing.
"""

from jsonschema import validate
from pathlib import Path

from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, APIC

import json
import pprint
import sys
import os
import subprocess
import requests


# ******
# Paths

YOUTUBE_DL = Path.cwd() / ".venv" / "Scripts" / "youtube-dl.exe"
DOWNLOAD_ARCHIVE = Path.cwd() / "data" / "metadata.sqlite3"

# ******
# Sets up logger
LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # Doesn't disable other loggers that might be active
    "formatters": {
        "default": {
            "format": "[%(levelname)s][%(funcName)s] | %(asctime)s | %(message)s",
        },
        "simple": {  # Used for console logging
            "format": "[%(levelname)s][%(funcName)s] | %(message)s",
        },
    },
    "handlers": {
        "logfile": {
            "class": "logging.FileHandler",  # Basic file handler
            "formatter": "default",
            "level": "WARNING",
            "filename": (Path.cwd() / "logfile.txt").as_posix(),
            "mode": "a",
            "encoding": "utf-8",
        },
        "console": {
            "class": "logging.StreamHandler",  # Basic stream handler
            "formatter": "simple",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {  # Simple program, so root logger uses all handlers
        "level": "DEBUG",
        "handlers": [
            "logfile",
            "console",
        ]
    }
}

# ***********************
# Functions

def download_audio_with_metadata(url: str) -> None:
    """Downloads the specified Youtube video as an audio file with embedded metadata.

    Args:
        url (str): Valid Youtube video URL
    """
    
    callResponse = subprocess.run(
                        [
                            YOUTUBE_DL,
                            "--embed-thumbnail",
                            "--add-metadata",
                            "--extract-audio",
                            "-o",
                            (Path.cwd() / "data" / "%(title)s.%(ext)s").as_posix(),
                            url,
                        ], shell=False
                    )
    
    if not callResponse.returncode == 0:
        logger.error("Subprocess call failed for url `%s` when attempting to download video with metadata with code: %i" % (str(url), callResponse.returncode))
        

def fetch_metadata(url: str) -> dict:
    """Fetches metadata for a youtube video using Youtube-dl. This metadata is returned as a dict.

    Args:
        url (str): Valid Youtube video URL.

    Returns:
        dict: Dict of video metadata.
    """
    
    metadata = {}
    
    # ---
    # Gets metadata in json format (in bytes)
    callResponse = subprocess.run(
                        [
                            YOUTUBE_DL,
                            "-j",
                            url,
                        ], stdout=subprocess.PIPE, shell=False
                    )
    
    # **
    # Checks if subprocess call was successful
    if callResponse.returncode == 0:
        try:
            metadata = json.loads(callResponse.stdout)
        except(json.decoder.JSONDecodeError):
            # Most likely fetches metadata for multiple videos (playlist), so this sketchily turns the bytes object to represent a list of dicts.
            metadata = json.loads(b"[" + callResponse.stdout.replace(b"}\n{", b"},{").replace(b"}\n", b"}") + b"]")
        except:
            logger.error("Something went wrong :(")
    else:
        logger.error("Subprocess call failed for url `%s` when attempting to write metadata with code: %i" % (str(url), callResponse.returncode))

    return metadata


def download_thumbnail(url: str):
    """Writes thumbnail to disk using Youtube-dl.

    Args:
        url (str): Valid Youtube video URL.
    """
    callResponse = subprocess.run(
                        [
                            YOUTUBE_DL,
                            "--write-thumbnail",
                            "--skip-download",
                            "-o",
                            (Path.cwd() / "data" / "%(title)s.%(ext)s").as_posix(),
                            url,
                        ], shell=False
                    )
    
    if not callResponse.returncode == 0:
        logger.error("Subprocess call failed for url `%s` when attempting to write thumbnail with code: %i" % (str(url), callResponse.returncode))


def set_m4a_metadata(file_path: Path, file_metadata: dict):
    """Sets audio metadata using Mutagen for m4a files.

    Args:
        file_metadata (dict): Dict of Youtube video metadata.
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
    
    set_cover(file_path, file_metadata["thumbnail"])
    
    tags.save(file_path.as_posix())
    
    
def set_cover(file_path: Path, cover: str):
    """Sets cover art of file to image.
    Credit to: https://stackoverflow.com/questions/53998371/running-into-problems-setting-cover-art-for-mp4-files-using-python-and-mutagen

    Args:
        file_path (Path): Path to file.
        cover (str): Path to image to use as cover art.
    """
    
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
    

# ***********************
# Execute Program
if __name__ == "__main__":
    import logging.config
    logging.disable(logging.DEBUG)
    logging.config.dictConfig(LOGGER_CONFIG)
    
    logger = logging.getLogger(__name__)


    # ***********
    # Obtains necessary resources
    # download_audio_with_metadata(r"https://www.youtube.com/watch?v=Ussqi3nagrQ")
    
    # file_metadata = fetch_metadata(r"https://www.youtube.com/watch?v=MhVChKHGoxs")
    
    # json_meta = json.dumps(file_metadata, indent=4)  # Serializes json
    # with (Path.cwd() / "meta.json").open("w") as outfile:
    #     outfile.write(json_meta)
    
    # download_thumbnail(r"https://www.youtube.com/watch?v=MhVChKHGoxs")
    
    # ***********
    # Changes metadata
    
    # pprint.pprint(os.listdir((Path.cwd() / "data").as_posix()))
    # file_names_and_urls = {
    #     'My_Youtube_Video.m4a': "https://www.youtube.com/watch?v=...",
    # }
    
    # for file, url in file_names_and_urls.items():
    #     # file_metadata = fetch_metadata(url)
    #     # set_m4a_metadata(Path.cwd() / "data" / file, file_metadata)
    #     # print("Set metadata for file: %s" % (file))
        
    #     download_thumbnail(url)

    # file_path = Path.cwd() / "data" / "My_Youtube_File.m4a"
    # file_url = r"https://www.youtube.com/watch?v=..."
    
    # file_metadata = fetch_metadata(file_url)
    
    # # json_meta = json.dumps(file_metadata, indent=4)  # Serializes json
    # # with (Path.cwd() / "meta.json").open("w") as outfile:
    # #     outfile.write(json_meta)
    
    # # download_thumbnail(file_url)
    
    # set_m4a_metadata(file_path, file_metadata)
    
    # # ***
    # # If downloading a single video
    file_url = "https://www.youtube.com/playlist?list=..."
    
    download_audio_with_metadata(file_url)
    # # file_metadata = fetch_metadata(file_url)
    
    # # Get file path then set metadata
    # # set_m4a_metadata(file_path, file_metadata)
  
