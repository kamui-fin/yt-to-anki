import os
import sys
import shutil
from glob import glob
from typing import List

import yt_dlp as youtube_dl

from .models import GenerateVideoTask
from .subtitles_extractor import SubtitleRange, YouTubeSubtitlesExtractor
from .errors import NoSubtitlesException

sys.stderr.isatty = lambda: False


class YouTubeDownloadResult:
    def __init__(
        self,
        video_title: str,
        subtitles: List[SubtitleRange],
        path_to_video: str,
        path_to_subtitles_file: str,
    ):
        assert isinstance(video_title, str), video_title
        assert isinstance(subtitles, list), subtitles
        assert isinstance(path_to_video, str), path_to_video
        assert isinstance(path_to_subtitles_file, str), path_to_subtitles_file
        assert os.path.isfile(path_to_video), path_to_video
        assert os.path.isfile(path_to_subtitles_file), path_to_subtitles_file
        self.video_title: str = video_title
        self.subtitles: List[SubtitleRange] = subtitles
        self.path_to_video: str = path_to_video
        self.path_to_subtitles_file: str = path_to_subtitles_file


class YouTubeClient:
    @staticmethod
    def download_video_files(
        video_task: GenerateVideoTask, on_progress
    ) -> YouTubeDownloadResult:
        print(
            f"yt2srs: YouTubeClient: downloading video: "
            f"{video_task.youtube_video_url}"
        )

        YouTubeClient._download_subtitles(
            video_task=video_task, on_progress=on_progress
        )
        video_info = YouTubeClient._download_video(
            video_task=video_task, on_progress=on_progress
        )
        title = video_info["title"]

        print(f"yt2srs: YouTubeClient: downloaded video: {title}")

        path_to_video = glob(video_task.path_to_downloaded_videos + "/*")[0]
        path_to_subtitles_file = glob(video_task.path_to_downloaded_subtitles + "/*")[0]

        subs: List[SubtitleRange] = YouTubeSubtitlesExtractor._parse_subs(
            path_to_subtitles_file
        )

        result = YouTubeDownloadResult(
            video_title=title,
            subtitles=subs,
            path_to_video=path_to_video,
            path_to_subtitles_file=path_to_subtitles_file,
        )
        return result

    @staticmethod
    def _download_subtitles(video_task: GenerateVideoTask, on_progress):
        if os.path.exists(video_task.path_to_downloaded_subtitles):
            shutil.rmtree(video_task.path_to_downloaded_subtitles)
        subtitle_output_file_template = os.path.join(
            video_task.path_to_downloaded_subtitles, "%(title)s-%(id)s.%(ext)s"
        )
        ydl_opts = {
            "subtitleslangs": [video_task.language],
            "skip_download": True,
            "writesubtitles": True,
            "outtmpl": subtitle_output_file_template,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [on_progress],
        }
        print(
            f"yt2srs: YouTubeClient: "
            f"downloading video subtitles with options: "
            f"{video_task.youtube_video_url} {ydl_opts}"
        )
        ydl = youtube_dl.YoutubeDL(ydl_opts)
        ydl.download([video_task.youtube_video_url])

        if not glob(video_task.path_to_downloaded_subtitles + "/*"):
            if video_task.fallback:
                opts_no_lang = {**ydl_opts, "writeautomaticsub": True}
                print(
                    f"yt2srs: YouTubeClient: "
                    f"downloading video subtitles in fallback mode with "
                    f"automatic subtitles: "
                    f"{video_task.youtube_video_url} {opts_no_lang}"
                )
                ydl = youtube_dl.YoutubeDL(opts_no_lang)
                ydl.download([video_task.youtube_video_url])
            else:
                raise NoSubtitlesException

    @staticmethod
    def _download_video(video_task: GenerateVideoTask, on_progress):
        if os.path.exists(video_task.path_to_downloaded_videos):
            shutil.rmtree(video_task.path_to_downloaded_videos)
        video_output_file_template = os.path.join(
            video_task.path_to_downloaded_videos, "%(title)s-%(id)s.%(ext)s"
        )
        vid_opts = {
            "no_color": True,
            # Careful with this line. When the warnings are enabled, the program
            # crashes in youtube-dl code with:
            # """
            # if not self.params.get('no_color')
            # and self._err_file.isatty()
            # and compat_os_name != 'nt':
            # """
            # AttributeError: 'ErrorHandler' object has no attribute 'isatty'
            # The problem is that Anki modifies the sys.stderr with a custom
            # Error Handler which does not support the methods like isatty()
            # and flush().
            # https://github.com/kamui-fin/yt2srs/issues/1
            # https://github.com/ytdl-org/youtube-dl/issues/28914
            "no_warnings": True,
            "outtmpl": video_output_file_template,
            "quiet": True,
            "progress_hooks": [on_progress],
        }
        print(
            f"yt2srs: YouTubeClient: "
            f"downloading video with options: "
            f"{video_task.youtube_video_url} {vid_opts}"
        )
        ydl = youtube_dl.YoutubeDL(vid_opts)
        ydl.download([video_task.youtube_video_url])

        print(
            f"yt2srs: YouTubeClient: "
            f"downloading video information: {video_task.youtube_video_url}"
        )
        video_info = ydl.extract_info(video_task.youtube_video_url, download=False)
        return video_info
