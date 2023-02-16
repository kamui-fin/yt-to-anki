import os
import datetime
from typing import Optional, List
from dataclasses import dataclass

from anki.collection import Collection

from ytanki.utils import get_addon_directory


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
    fields: FieldsConfiguration
    video_path: str = os.path.join(get_addon_directory(), "vid")
    subtitle_path: str = os.path.join(get_addon_directory(), "subs")


@dataclass
class SubtitleRange:
    text: str
    time_start: datetime.datetime
    time_end: datetime.datetime
    # Injected later when the picture and audio are produced.
    picture_path: Optional[str] = None
    audio_path: Optional[str] = None

    def add_paths_to_picture_and_audio(self, path_to_picture: str, path_to_audio: str):
        self.picture_path = path_to_picture
        self.audio_path = path_to_audio


@dataclass
class YouTubeDownloadResult:
    video_title: str
    subtitles: List[SubtitleRange]
    video_path: str
    subtitle_path: str
