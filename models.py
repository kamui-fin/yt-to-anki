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
        dimensions: str,
        limit: int,
        collection: Collection,
        output_dir: str,
        fields: FieldsConfiguration,
    ):
        assert isinstance(youtube_video_url, str)
        assert isinstance(language, str)
        assert isinstance(fallback, bool)
        assert isinstance(dimensions, str)
        assert isinstance(limit, int)
        assert isinstance(collection, Collection)
        assert isinstance(output_dir, str)
        assert isinstance(fields, FieldsConfiguration)
        self.youtube_video_url: str = youtube_video_url
        self.language: str = language
        self.fallback: bool = fallback
        self.dimensions: str = dimensions
        self.limit: int = limit
        self.collection: Collection = collection
        self.output_dir: str = output_dir
        self.fields: FieldsConfiguration = fields
