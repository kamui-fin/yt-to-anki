import os
import re
import sys
import shutil
from glob import glob
from typing import List

import yt_dlp as youtube_dl

from .models import GenerateVideoTask, YouTubeDownloadResult
from .subtitles_extractor import SubtitleRange, YouTubeSubtitlesExtractor
from .errors import NoSubtitlesException

sys.stderr.isatty = lambda: False


class YouTubeClient:
    @staticmethod
    def is_valid_link(link: str) -> bool:
        exp = re.compile(
            r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?"
        )
        return bool(exp.match(link))

    @staticmethod
    def get_subtitle_langs(link: str, fallback: bool):
        def fetch_langs(captions):
            info = {
                lang_code: tracks[0]["name"]
                for lang_code, tracks in captions.items()
                if tracks and "name" in tracks[0]
            }
            return {v: k for k, v in info.items()}

        vid_opts = {
            "skip_download": True,
            "listsubtitles": True,
            "no_color": True,
            "no_warnings": True,
            "quiet": True,
        }
        ydl = youtube_dl.YoutubeDL(vid_opts)
        video_info = ydl.extract_info(link, download=False)
        keys = list(video_info.keys())

        if not video_info or (
            "subtitles" not in keys and "automatic_captions" not in keys
        ):
            return {}

        auto = fetch_langs(video_info["automatic_captions"])
        manual = fetch_langs(video_info["subtitles"])

        if not manual:
            return auto if fallback else {}
        else:
            return manual

    @staticmethod
    def download_video_files(
        video_task: GenerateVideoTask, on_progress
    ) -> YouTubeDownloadResult:
        print(
            f"yt-to-anki: YouTubeClient: downloading video: "
            f"{video_task.youtube_video_url}"
        )

        YouTubeClient._download_subtitles(video_task, on_progress)
        title = YouTubeClient._download_video(video_task, on_progress)

        print(f"yt-to-anki: YouTubeClient: downloaded video: {title}")

        path_to_video = glob(video_task.video_path + "/*")[0]
        path_to_subtitles_file = glob(video_task.subtitle_path + "/*")[0]

        subs: List[SubtitleRange] = YouTubeSubtitlesExtractor.parse_subtitles(
            path_to_subtitles_file
        )
        if video_task.optimize_by_punctuation:
            subs = YouTubeSubtitlesExtractor.optimize_subtitles(subs)

        result = YouTubeDownloadResult(
            f"{title} - {video_task.language}",
            subs,
            path_to_video,
            path_to_subtitles_file,
        )
        return result

    @staticmethod
    def _download_subtitles(video_task: GenerateVideoTask, on_progress):
        if os.path.exists(video_task.subtitle_path):
            shutil.rmtree(video_task.subtitle_path)

        subtitle_output_file_template = os.path.join(
            video_task.subtitle_path, "%(title)s-%(id)s.%(ext)s"
        )
        ydl_opts = {
            "subtitleslangs": [video_task.language],
            "skip_download": True,
            "writesubtitles": True,
            "outtmpl": subtitle_output_file_template,
            "subtitlesformat": "vtt",
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [on_progress],
        }
        print(
            f"yt-to-anki: YouTubeClient: "
            f"downloading video subtitles with options: "
            f"{video_task.youtube_video_url} {ydl_opts}"
        )
        ydl = youtube_dl.YoutubeDL(ydl_opts)
        ydl.download([video_task.youtube_video_url])

        if not glob(video_task.subtitle_path + "/*"):
            if video_task.fallback:
                opts_no_lang = {**ydl_opts, "writeautomaticsub": True}
                print(
                    f"yt-to-anki: YouTubeClient: "
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
        if os.path.exists(video_task.video_path):
            shutil.rmtree(video_task.video_path)

        video_output_file_template = os.path.join(
            video_task.video_path, "%(title)s-%(id)s.%(ext)s"
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
            # https://github.com/kamui-fin/yt-to-anki/issues/1
            # https://github.com/ytdl-org/youtube-dl/issues/28914
            "no_warnings": True,
            "outtmpl": video_output_file_template,
            "quiet": True,
            "progress_hooks": [on_progress],
        }
        print(
            f"yt-to-anki: YouTubeClient: "
            f"downloading video with options: "
            f"{video_task.youtube_video_url} {vid_opts}"
        )
        ydl = youtube_dl.YoutubeDL(vid_opts)
        ydl.download([video_task.youtube_video_url])

        print(
            f"yt-to-anki: YouTubeClient: "
            f"downloading video information: {video_task.youtube_video_url}"
        )
        video_info = ydl.extract_info(video_task.youtube_video_url, download=False)
        return video_info["title"] if video_info else "YouTube Video"
