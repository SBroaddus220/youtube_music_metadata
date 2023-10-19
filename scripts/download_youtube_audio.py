#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to download audio from Youtube videos with embedded metadata using yt-dlp.
"""

import json
import logging
import argparse
import logging.config

# Add root project directory to path
import sys
from pathlib import Path
sys.path.append((Path(__file__).parent.parent.resolve()).as_posix())

from youtube_music_metadata.utilities import (
    download_audio_with_metadata, 
    load_logging_config, 
    fetch_metadata,
    download_thumbnail,
    set_m4a_metadata,
    set_opus_metadata
    )

# **********
# Sets up logger
logger = logging.getLogger(__name__)


# **********
def main():
    import logging.config
    
    parser = argparse.ArgumentParser(
        description="Download audio from Youtube videos with embedded metadata using yt-dlp",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # ****
    # Arguments
    parser.add_argument("url", type=str, help="URL of Youtube video.")
    parser.add_argument("--output_file_path", type=Path, 
                        help="File path to save audio file/thumbnail to. Defaults to current working directory with filename of video title.")
    
    download_audio_group = parser.add_argument_group("Download audio with metadata")
    download_audio_group.add_argument("--no_m4a_metadata", action="store_true", default = False, 
                    help="Do not set metadata for the downloaded audio file with metadata.")
    
    
    utilities_group = parser.add_argument_group("Utilities to interact with Youtube videos and metadata")
    utilities_group.add_argument("--metadata-only", action="store_true", 
                        help="Only fetch the metadata for the YouTube video without downloading it.")
    
    utilities_group.add_argument("--download-thumbnail", action="store_true", default = False,
                        help="Download the thumbnail of the YouTube video.")
    
    utilities_group.add_argument("--set-m4a-metadata", type=Path, 
                        help="Set metadata for the provided .m4a file path.")
    
    utilities_group.add_argument('--log-config', type=Path, default=None, 
                        help='Path to the logging config file.')
    
    
    args = parser.parse_args()
    
    # ****
    # Loads logging config
    if args.log_config and args.log_config.exists():
        LOGGER_CONFIG = load_logging_config(args.log_config)
    else:
        # Loads default logging config
        default_config_path = Path(__file__).parent.parent.resolve() / "config" / "default_logging_config.json"
        LOGGER_CONFIG = load_logging_config(default_config_path)

    logging.config.dictConfig(LOGGER_CONFIG)
    
    # ****
    # Handle the functionalities based on provided arguments
    if args.metadata_only:
        metadata = fetch_metadata(args.url)
        print(json.dumps(metadata, indent=4))  # Pretty print the metadata
    
    elif args.download_thumbnail:
        download_thumbnail(args.url)
    
    elif args.set_m4a_metadata:
        metadata = fetch_metadata(args.url)
        
        file_path = args.set_m4a_metadata
        file_extension = file_path.suffix.lower()
        if file_extension == ".m4a":
            set_m4a_metadata(file_path, metadata)
        elif file_extension == ".opus":
            set_opus_metadata(file_path, metadata)
        else:
            print(f"Unsupported file format: {file_extension}")
    
    else:
        download_audio_with_metadata(args.url, args.output_file_path)


# **********
if __name__ == "__main__":
    main()

