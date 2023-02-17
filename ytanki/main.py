import os
from pathlib import Path

from PyQt5 import QtCore
from aqt import mw
from aqt.utils import showCritical

from . import worker
from .constants import LANGUAGES
from .models import FieldsConfiguration, GenerateVideoTask
from .ui import Window
from .utils import has_ffmpeg, bool_to_string, string_to_bool


class MainWindow(Window):
    def __init__(self):
        super().__init__()
        settings_path = str(Path(os.path.abspath(__file__)).parent / "main.ini")
        self.settings = QtCore.QSettings(
            settings_path, QtCore.QSettings.Format.IniFormat
        )

    def setup_ui(self):
        langs = [""] + list(LANGUAGES.keys())
        notes = [""] + self.get_note_types()
        fields = [""]

        self.subs_lang_box.addItems(langs)
        self.note_box.addItems(notes)
        self.audio_box.addItems(fields)
        self.pic_box.addItems(fields)
        self.text_box.addItems(fields)

        self.generate_button.clicked.connect(self.generate)
        self.note_box.currentTextChanged.connect(self.fill_fields)
        self.read_settings()

    def fill_fields(self, note_type):
        fields = self.get_fields_for_note(note_type)
        self.audio_box.addItems(fields)
        self.pic_box.addItems(fields)
        self.text_box.addItems(fields)

    def get_note_types(self):
        return mw.col.models.allNames()

    def get_fields_for_note(self, note_type: str):
        fields = mw.col.db.list(
            "SELECT FIELDS.name FROM FIELDS INNER JOIN notetypes ON FIELDS.ntid = notetypes.id WHERE notetypes.name = ?",  # noqa: E501
            note_type,
        )
        return fields

    def generate(self):
        youtube_video_url = self.link_box.text()
        if not youtube_video_url.startswith("https://www.youtube.com/watch?v="):
            self.error("Invalid youtube link")
            return

        language = LANGUAGES.get(self.subs_lang_box.currentText(), None)
        if language is None:
            self.error("Please enter a language")
            return

        note_type = self.note_box.currentText()
        if not note_type:
            self.error("Please choose a note type")
            return

        text_field = self.text_box.currentText()
        audio_field = self.audio_box.currentText()
        picture_field = self.pic_box.currentText()

        if not text_field or not audio_field or not picture_field:
            self.error("Please enter all fields")
            return

        fallback = self.fallback_check.isChecked()
        optimize_by_punctuation = self.optimize_subtitles_check.isChecked()
        dimensions = f"{self.width_box.value()}x{self.height_box.value()}"
        limit = self.limit_box.value()

        # only write settings once all fields pass validation
        self.write_settings()

        fields: FieldsConfiguration = FieldsConfiguration(
            note_type,
            text_field,
            audio_field,
            picture_field,
        )
        task = GenerateVideoTask(
            youtube_video_url,
            language,
            fallback,
            optimize_by_punctuation,
            dimensions,
            limit,
            mw.col,
            fields,
        )
        worker.create_deck(task=task)

    def read_settings(self):
        self.settings.beginGroup("MainWindow")
        self.link_box.setText(self.settings.value("video_url", ""))
        self.subs_lang_box.setCurrentText(
            self.settings.value("subs_lang_box", "English")
        )

        self.note_box.setCurrentText(self.settings.value("note_box", ""))
        self.audio_box.setCurrentText(self.settings.value("audio_box", ""))
        self.pic_box.setCurrentText(self.settings.value("pic_box", ""))
        self.text_box.setCurrentText(self.settings.value("text_box", ""))

        self.width_box.setValue(int(self.settings.value("width", 240)))
        self.height_box.setValue(int(self.settings.value("height", 160)))
        self.limit_box.setValue(int(self.settings.value("limit", 0)))

        self.fallback_check.setChecked(
            string_to_bool(self.settings.value("fallback", False))
        )
        self.optimize_subtitles_check.setChecked(
            string_to_bool(self.settings.value("optimize_subtitles", False))
        )

        self.settings.endGroup()

    def write_settings(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("video_url", self.link_box.text())
        self.settings.setValue("subs_lang_box", self.subs_lang_box.currentText())

        self.settings.setValue("note_box", self.note_box.currentText())
        self.settings.setValue("audio_box", self.audio_box.currentText())
        self.settings.setValue("pic_box", self.pic_box.currentText())
        self.settings.setValue("text_box", self.text_box.currentText())

        self.settings.setValue("width", self.width_box.value())
        self.settings.setValue("height", self.height_box.value())
        self.settings.setValue("limit", self.limit_box.value())

        self.settings.setValue(
            "fallback", bool_to_string(self.fallback_check.isChecked())
        )
        self.settings.setValue(
            "optimize_subtitles",
            bool_to_string(self.optimize_subtitles_check.isChecked()),
        )

        self.settings.endGroup()
        self.settings.sync()

    @staticmethod
    def error(text, title="Error has occured"):
        showCritical(text, title=title)


def launch():
    mw.yt_anki_screen = screen = MainWindow()
    screen.setup_ui()
    # dependency check
    if not has_ffmpeg():
        showCritical("Linux or Mac users must install ffmpeg to PATH.")
    else:
        screen.show()
