import os
from subprocess import check_output
from pathlib import Path


home = os.path.dirname(os.path.abspath(__file__))


def get_windows_ffmpeg():
    return os.path.join(home, "ffmpeg/ffmpeg.exe")


def get_ffmpeg():
    return get_windows_ffmpeg() if os.name == "nt" else "ffmpeg"


def has_ffmpeg(command="ffmpeg"):
    if os.name == "nt":
        return Path(os.path.join(home, "ffmpeg/ffmpeg.exe")).exists()

    try:
        check_output(command, shell=True)
        return True
    except:
        return False
