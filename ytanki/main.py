import os
from pathlib import Path

from PyQt5 import QtCore, QtWidgets
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
        langs = [""] + list(LANGUAGES.values())
        notes = [""] + mw.col.models.allNames()
        fields = [""] + self.get_fields()

        self.subs_lang_box.addItems(langs)
        self.note_box.addItems(notes)
        self.audio_box.addItems(fields)
        self.pic_box.addItems(fields)
        self.text_box.addItems(fields)

        self.choose_dir_button.clicked.connect(self.choose_dir)
        self.generate_button.clicked.connect(lambda: self.generate())
        self.read_settings()

    def choose_dir(self):
        directory = str(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Output Folder")
        )
        self.output_box.setText(directory)

    def get_fields(self):
        fields = mw.col.db.all(
            "SELECT notetypes.name, FIELDS.name FROM FIELDS INNER JOIN notetypes ON FIELDS.ntid = notetypes.id"  # noqa: E501
        )
        return [f"{note_type}: {field_name}" for note_type, field_name in fields]

    def generate(self):
        # TODO: refactor to validation methods
        #       only show fields that are in the note
        youtube_video_url: str = str(self.link_box.text())
        if not youtube_video_url.startswith("https://www.youtube.com/watch?v="):
            self.error("Invalid youtube link")
            return

        try:
            language: str = {v: k for k, v in LANGUAGES.items()}[
                str(self.subs_lang_box.currentText())
            ]
        except KeyError:
            self.error("Please enter a language")
            return

        fallback: bool = self.fallback_check.isChecked()
        optimize_by_punctuation: bool = self.optimize_subtitles_check.isChecked()
        dimensions: str = f"{self.width_box.value()}x{self.height_box.value()}"
        limit: int = self.limit_box.value()

        output_dir: str = str(self.output_box.text())
        if not os.path.isdir(output_dir):
            self.error("Invalid output folder")
            return

        note_type: str = str(self.note_box.currentText())
        if not note_type:
            self.error("Please choose a note type")
            return

        text_field: str = self.text_box.currentText().split(": ")[-1]
        audio_field: str = self.audio_box.currentText().split(": ")[-1]
        picture_field: str = self.pic_box.currentText().split(": ")[-1]

        if not text_field or not audio_field or not picture_field:
            self.error("Please enter all fields")
            return

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
            output_dir,
            fields,
        )
        worker.create_deck(task=task)

    def read_settings(self):
        self.settings.beginGroup("MainWindow")
        self.link_box.setText(self.settings.value("video_url", ""))
        self.output_box.setText(self.settings.value("output_dir", ""))
        self.subs_lang_box.setCurrentText(
            self.settings.value("subs_lang_box", LANGUAGES.get("en"))
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
        self.settings.setValue("output_dir", self.output_box.text())
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
    screen = MainWindow()
    screen.setup_ui()
    # dependency check
    if not has_ffmpeg():
        showCritical("Linux or Mac users must install ffmpeg to PATH.")
    else:
        screen.show()
