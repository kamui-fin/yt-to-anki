import os
from datetime import datetime
from typing import List

from ytanki.subtitles_extractor import SubtitleRange, YouTubeSubtitlesExtractor

path_to_this_test_folder = os.path.abspath(os.path.dirname(__file__))
path_to_the_subtitles_file = os.path.join(path_to_this_test_folder, "subtitles.en.vtt")


def time_from(string):
    return datetime.strptime(string, "%H:%M:%S.%f")


def test_01_parsing_subtitles():
    # https://www.youtube.com/watch?v=GfF2e0vyGM4
    subtitles: List[SubtitleRange] = YouTubeSubtitlesExtractor.parse_subtitles(
        path_to_the_subtitles_file
    )
    assert subtitles[0].text == "What if doing well in school and in life"

    optimized_subtitles = YouTubeSubtitlesExtractor.optimize_subtitles(subtitles)

    assert optimized_subtitles[0].time_start == time_from("00:00:00.049")
    assert optimized_subtitles[0].time_end == time_from("00:00:09.630")
    assert optimized_subtitles[0].text == (
        "What if doing well in school and in life depends on much more "
        "than your ability to learn quickly and easily?"
    )

    assert optimized_subtitles[1].time_start == time_from("00:00:09.630")
    assert optimized_subtitles[1].time_end == time_from("00:00:20.259")
    assert (
        optimized_subtitles[1].text
        == (
            "I started studying kids and adults in all kinds of super challenging "
            "settings, and in every study my question was, "
            '"Who is successful here and why?"'
        ).strip()
    )

    assert optimized_subtitles[13].time_start == time_from("00:01:08.760")
    assert optimized_subtitles[13].time_end == time_from("00:01:21.640")
    assert (
        optimized_subtitles[13].text
        == (
            "Grit is sticking with your future, day in, day out, not just "
            "for the week, not just for the month, but for years, and working "
            "really hard to make that future a reality."
        ).strip()
    )
