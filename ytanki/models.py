import os
from typing import Optional, List
from dataclasses import dataclass

from anki.collection import Collection


@dataclass
class FieldsConfiguration:
    note_type: str
    text_field: str
    audio_field: str
    picture_field: str


@dataclass
class GenerateVideoTask:
    youtube_video_url: str
    language: str
    fallback: bool
    optimize_by_punctuation: bool
    dimensions: str
    limit: int
    collection: Collection
    output_dir: str
    fields: FieldsConfiguration
    home: str = os.path.dirname(os.path.abspath(__file__))
    path_to_downloaded_videos: str = os.path.join(home, "vid")
    path_to_downloaded_subtitles: str = os.path.join(home, "subs")


@dataclass
class SubtitleRange:
    text: str
    time_start: str
    time_end: str
    # Injected later when the picture and audio are produced.
    path_to_picture: Optional[str] = None
    path_to_audio: Optional[str] = None

    def add_paths_to_picture_and_audio(self, path_to_picture: str, path_to_audio: str):
        self.path_to_picture = path_to_picture
        self.path_to_audio = path_to_audio


@dataclass
class YouTubeDownloadResult:
    video_title: str
    subtitles: List[SubtitleRange]
    path_to_video: str
    path_to_subtitles_file: str
