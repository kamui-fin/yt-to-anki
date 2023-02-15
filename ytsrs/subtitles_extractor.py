import os
import pathlib
import re
from typing import List, Optional


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
    def parse_subtitles(filename) -> List[SubtitleRange]:
        subtitles: List[SubtitleRange] = []
        text = pathlib.Path(filename).read_text(encoding="utf-8")
        chunked = re.split("\n\n", text)[1:]
        for chunk in chunked:
            try:
                start, end = re.findall(
                    "(\\d+:\\d+:\\d+\\.\\d+) --> (\\d+:\\d+:\\d+\\.\\d+).*\n", chunk
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

    @staticmethod
    def optimize_subtitles(subtitles: List[SubtitleRange]) -> List[SubtitleRange]:
        assert isinstance(subtitles, list)
        # Nothing to optimize.
        if len(subtitles) < 2:
            return subtitles

        def merge(subtitle1: SubtitleRange, subtitle2: SubtitleRange):
            if subtitle1 == subtitle2:
                return
            subtitle1.time_end = subtitle2.time_end
            subtitle1.text += " " + subtitle2.text

        optimized_subtitles: List[SubtitleRange] = []
        current_subtitle: Optional[SubtitleRange] = None
        for subtitle in subtitles:
            # Trim subtitle just in case. This mutates the objects but
            # is ok like this for now.
            subtitle.text = subtitle.text.strip()

            if current_subtitle is None:
                current_subtitle = subtitle
                optimized_subtitles.append(current_subtitle)

            if (
                subtitle.text.endswith(".")
                or subtitle.text.endswith("?")
                or subtitle.text.endswith('?"')
            ):
                merge(current_subtitle, subtitle)
                current_subtitle = None
            else:
                merge(current_subtitle, subtitle)

        return optimized_subtitles
