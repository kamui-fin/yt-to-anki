import os
import datetime
from subprocess import check_output, CalledProcessError
import platform
import subprocess
from pathlib import Path
from typing import List


home = os.path.dirname(os.path.abspath(__file__))


def get_windows_ffmpeg():
    return os.path.join(home, "ffmpeg.exe")


def get_ffmpeg():
    return get_windows_ffmpeg() if os.name == "nt" else "ffmpeg"


def has_ffmpeg():
    if os.name == "nt":
        return Path(os.path.join(home, "ffmpeg.exe")).exists()
    else:
        try:
            subprocess.run(
                ["which", "ffmpeg"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            pass

        if platform.system() == "Darwin":
            brew_ffmpeg_path = "/usr/local/bin/ffmpeg"
            if os.path.exists(brew_ffmpeg_path):
                return True

        return False


def bool_to_string(bool_value: bool):
    return "true" if bool_value else "false"


def string_to_bool(string_value: str):
    return string_value == "true"


def get_timestamp(time: str) -> datetime.datetime:
    return datetime.datetime.strptime(time, "%H:%M:%S.%f")


def with_limit(array: List, limit: int) -> List:
    if limit == 0:
        return array
    return array[:limit]


def get_addon_directory() -> str:
    return os.path.dirname(os.path.abspath(__file__))
