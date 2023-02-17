from pathlib import Path
from subprocess import check_output
import tempfile

from .utils import get_ffmpeg


class Ffmpeg:
    def __init__(self, subtitle, video_path, video_title):
        self.time_diff = (subtitle.time_end - subtitle.time_start).total_seconds()
        media_path_prefix = Path(tempfile.gettempdir()).joinpath(
            f"{video_title}_\
                  {str(subtitle.time_start).replace('.','_').replace(':','_')}_\
                  {str(self.time_diff).replace('.','_').replace(':','_')}",
        )
        self.audio_path = str(media_path_prefix.with_suffix(".mp3"))
        self.picture_path = str(media_path_prefix.with_suffix(".jpeg"))
        self.video_path = video_path
        self.subtitle = subtitle
        self.ffmpeg = get_ffmpeg()

    def get_picture(self, dimensions):
        picture_command = (
            self.ffmpeg
            + " -y "  # Overwrite output file.
            + " -ss "
            + str(self.subtitle.time_start.time())
            + " -i "
            + '"'
            + self.video_path
            + '" '
            + "-s "
            + dimensions
            + " -vframes 1 -q:v 2 "
            + "-loglevel quiet "
            + '"'
            + self.picture_path
            + '"'
        )
        check_output(picture_command, shell=True)

    def get_audio(self):
        audio_command = (
            self.ffmpeg
            + " -y "  # Overwrite output file.
            + " -ss "
            + str(self.subtitle.time_start.time())
            + " -i "
            + '"'
            + self.video_path
            + '"'
            + " -t 00:"
            + str(self.time_diff)
            + " -loglevel quiet"
            + ' "'
            + self.audio_path
            + '"'
        )
        check_output(audio_command, shell=True)

    # mutates object, bad practice?
    def fill_sub_media(self):
        self.subtitle.add_paths_to_picture_and_audio(self.picture_path, self.audio_path)

    def generate_media(self, dimensions):
        self.get_picture(dimensions)
        self.get_audio()
        self.fill_sub_media()
