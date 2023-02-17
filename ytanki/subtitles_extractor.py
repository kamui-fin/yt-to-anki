from typing import List, Optional
import webvtt

from .utils import get_timestamp

from .models import SubtitleRange


class YouTubeSubtitlesExtractor:
    @staticmethod
    def parse_subtitles(filename) -> List[SubtitleRange]:
        subtitles: List[SubtitleRange] = [
            SubtitleRange(
                text=caption.text.replace("\n", " ").strip(),
                time_start=get_timestamp(caption.start),
                time_end=get_timestamp(caption.end),
            )
            for caption in webvtt.read(filename)
        ]
        without_duplicates = []
        seen_subs = set()
        for sub in subtitles:
            if sub.text not in seen_subs:
                without_duplicates.append(sub)
                seen_subs.add(sub.text)

        return without_duplicates

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
