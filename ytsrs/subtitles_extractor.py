import os
from typing import List, Optional
import webvtt


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
        subtitles: List[SubtitleRange] = [
            SubtitleRange(
                text=caption.text.replace("\n", " "),
                time_start=caption.start,
                time_end=caption.end,
            )
            for caption in webvtt.read(filename)
        ]
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
