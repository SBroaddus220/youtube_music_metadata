# youtube_music_metadata

## Description
Simple Python script to download audio and attach metadata from Youtube videos. Meant to be used with music videos.

## Installation
This package uses Poetry. Please navigate to the root directory and perform the following:
```
poetry install
```

This is necessary to install dependencies and to install the shim scripts detailed in the `pyproject.toml` file.

## Usage
Example usage is documented in the provided scripts. These scripts are designed as shims, meaning you can find compiled command line utilities for these scripts in the poetry virtual environment for this project. 

To find the virtual environment path, use the following:
```
poetry env list --full-path
```
Find the scripts as named in the `pyproject.toml` file and execute as normal command line utilities. Use the `--help` flag for help.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
