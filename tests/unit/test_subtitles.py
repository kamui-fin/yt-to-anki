from anki.collection import Collection
from ytsrs.client_youtube import YouTubeClient
from ytsrs.models import FieldsConfiguration, GenerateVideoTask
from ytsrs.errors import NoSubtitlesException

from unittest.mock import MagicMock
import pytest


def test_safe_handle_no_fallback_no_subtitles():
    with pytest.raises(NoSubtitlesException):
        task = GenerateVideoTask(
            youtube_video_url="https://www.youtube.com/watch?v=7CWBdYbfmqw",
            language="en",
            fallback=False,
            optimize_by_punctuation=False,
            # mocked
            dimensions="",
            limit=0,
            collection=MagicMock(spec=Collection),
            output_dir="",
            fields=MagicMock(spec=FieldsConfiguration),
        )
        YouTubeClient.download_video_files(task, on_progress=None)
