import os
from typing import List

from subtitles_extractor import YouTubeSubtitlesExtractor, SubtitleRange

path_to_this_test_folder = os.path.abspath(os.path.dirname(__file__))
path_to_the_subtitles_file = os.path.join(
    path_to_this_test_folder, "subtitles.en.vtt"
)


def test_01_parsing_subtitles():
    # https://www.youtube.com/watch?v=GfF2e0vyGM4
    subtitles: List[SubtitleRange] = YouTubeSubtitlesExtractor._parse_subs(
        path_to_the_subtitles_file
    )

    assert subtitles[0].text == "What if doing well in school and in life"
    assert subtitles[21].text == "Grit is sticking with your future, "
