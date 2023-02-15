import os
from subprocess import check_output, CalledProcessError
from pathlib import Path


home = os.path.dirname(os.path.abspath(__file__))

# For Linux and macOS, check if the ffmpeg is present in the PATH.
# Running with --help because without, ffmpeg exists with non-zero.
LINUX_MACOS_FFMPEG_CHECK_COMMAND = "ffmpeg --help"


def get_windows_ffmpeg():
    return os.path.join(home, "ffmpeg/ffmpeg.exe")


def get_ffmpeg():
    return get_windows_ffmpeg() if os.name == "nt" else "ffmpeg"


def has_ffmpeg(command=LINUX_MACOS_FFMPEG_CHECK_COMMAND):
    if os.name == "nt":
        return Path(os.path.join(home, "ffmpeg/ffmpeg.exe")).exists()

    try:
        check_output(command, shell=True)
        return True
    except (FileNotFoundError, CalledProcessError):
        return False


def bool_to_string(bool_value: bool):
    return "true" if bool_value else "false"


def string_to_bool(string_value: str):
    return string_value == "true"
