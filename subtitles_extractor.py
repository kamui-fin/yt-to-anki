import os
import pathlib
import re
from typing import Optional, List


class SubtitleRange:
    def __init__(self, text: str, time_start: str, time_end: str):
        self.text: str = text
        self.time_start: str = time_start
        self.time_end: str = time_end

        # Injected later when the picture and audio are produced.
        self.path_to_picture: Optional[str] = None
        self.path_to_audio: Optional[str] = None

    def add_paths_to_picture_and_audio(self, path_to_picture: str, path_to_audio: str):
        assert os.path.isfile(path_to_picture), path_to_picture
        assert os.path.isfile(path_to_audio), path_to_audio
        self.path_to_picture = path_to_picture
        self.path_to_audio = path_to_audio


class YouTubeSubtitlesExtractor:
    @staticmethod
    def _parse_subs(filename) -> List[SubtitleRange]:
        subtitles: List[SubtitleRange] = []
        text = pathlib.Path(filename).read_text(encoding="utf-8")
        chunked = re.split("\n\n", text)[1:]
        for chunk in chunked:
            try:
                start, end = re.findall(
                    "(\d+:\d+:\d+\.\d+) --> (\d+:\d+:\d+\.\d+).*\n", chunk
                )[0]
            except IndexError:
                break  # reached end of subs
            line = " ".join(chunk.split("\n")[1:])
            subtitles.append(
                SubtitleRange(
                    text=line,
                    time_start=start,
                    time_end=end,
                )
            )
        return subtitles
