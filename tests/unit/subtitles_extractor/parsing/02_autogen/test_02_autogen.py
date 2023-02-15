import os
from typing import List

from ytsrs.subtitles_extractor import SubtitleRange, YouTubeSubtitlesExtractor

path_to_this_test_folder = os.path.abspath(os.path.dirname(__file__))
path_to_the_subtitles_file = os.path.join(path_to_this_test_folder, "subtitles.en.vtt")


def test_02_autogen_removes_structure():
    subtitles: List[SubtitleRange] = YouTubeSubtitlesExtractor.parse_subtitles(
        path_to_the_subtitles_file
    )
    assert "<c>" not in subtitles[0].text
    assert "</c>" not in subtitles[0].text


def test_02_avoid_duplicates():
    subtitles: List[SubtitleRange] = YouTubeSubtitlesExtractor.parse_subtitles(
        path_to_the_subtitles_file
    )
    texts = [sub.text for sub in subtitles]
    assert len(set(texts)) == len(texts)
