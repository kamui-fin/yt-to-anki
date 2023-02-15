import os

from anki.collection import Collection


class FieldsConfiguration:
    def __init__(
        self,
        note_type: str,
        text_field: str,
        audio_field: str,
        picture_field: str,
    ):
        self.note_type: str = note_type
        self.text_field: str = text_field
        self.audio_field: str = audio_field
        self.picture_field: str = picture_field


class GenerateVideoTask:
    def __init__(
        self,
        youtube_video_url: str,
        language: str,
        fallback: bool,
        optimize_by_punctuation: bool,
        dimensions: str,
        limit: int,
        collection: Collection,
        output_dir: str,
        fields: FieldsConfiguration,
    ):
        assert isinstance(youtube_video_url, str)
        assert isinstance(language, str)
        assert isinstance(fallback, bool)
        assert isinstance(optimize_by_punctuation, bool)
        assert isinstance(dimensions, str)
        assert isinstance(limit, int)
        assert isinstance(collection, Collection)
        assert isinstance(output_dir, str)
        assert isinstance(fields, FieldsConfiguration)
        self.youtube_video_url: str = youtube_video_url
        self.language: str = language
        self.fallback: bool = fallback
        self.optimize_by_punctuation: bool = optimize_by_punctuation
        self.dimensions: str = dimensions
        self.limit: int = limit
        self.collection: Collection = collection
        self.output_dir: str = output_dir
        self.fields: FieldsConfiguration = fields

        self.home = os.path.dirname(os.path.abspath(__file__))
        self.path_to_downloaded_videos = os.path.join(self.home, "vid")
        self.path_to_downloaded_subtitles = os.path.join(self.home, "subs")
