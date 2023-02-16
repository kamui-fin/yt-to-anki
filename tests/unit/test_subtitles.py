# from anki.collection import Collection
# from ytanki.client_youtube import YouTubeClient
# from ytanki.models import FieldsConfiguration, GenerateVideoTask
# from ytanki.errors import NoSubtitlesException

# from unittest.mock import MagicMock
# import pytest

# test failing currently due to: https://github.com/yt-dlp/yt-dlp/issues/6253
# def test_safe_handle_no_fallback_no_subtitles():
#     with pytest.raises(NoSubtitlesException):
#         task = GenerateVideoTask(
#             youtube_video_url="https://www.youtube.com/watch?v=QC8iQqtG0hg",
#             language="en",
#             fallback=False,
#             optimize_by_punctuation=False,
#             # mocked
#             dimensions="",
#             limit=0,
#             collection=MagicMock(spec=Collection),
#             fields=MagicMock(spec=FieldsConfiguration),
#         )
#         YouTubeClient.download_video_files(task, on_progress=None)
