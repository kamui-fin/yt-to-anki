from pathlib import Path

from PyQt5 import QtCore, QtWidgets
from aqt import mw
from aqt.utils import showCritical


from . import worker
from .constants import LANGUAGES
from .models import FieldsConfiguration, GenerateVideoTask
from .utils import get_addon_directory, has_ffmpeg, bool_to_string, string_to_bool
from .client_youtube import YouTubeClient
from .gui import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)

        settings_path = str(Path(get_addon_directory()) / "main.ini")
        self.settings = QtCore.QSettings(
            settings_path, QtCore.QSettings.Format.IniFormat
        )

    def setup_ui(self):
        langs = list(LANGUAGES.keys())
        notes = self.get_note_types()

        self.language_field.addItems(langs)
        self.note_type_field.addItems(notes)

        self.fill_fields(self.note_type_field.currentText())

        self.generate_button.clicked.connect(self.generate)
        self.note_type_field.currentTextChanged.connect(self.fill_fields)
        self.read_settings()

    def fill_fields(self, note_type):
        fields = self.get_fields_for_note(note_type)

        self.audio_field.clear()
        self.audio_field.addItems(fields)

        self.picture_field.clear()
        self.picture_field.addItems(fields)

        self.text_field.clear()
        self.text_field.addItems(fields)

    def get_note_types(self):
        return mw.col.models.allNames()

    def get_fields_for_note(self, note_type: str):
        fields = mw.col.db.list(
            "SELECT FIELDS.name FROM FIELDS INNER JOIN notetypes ON FIELDS.ntid = notetypes.id WHERE notetypes.name = ?",
            note_type,
        )
        return fields

    def generate(self):
        youtube_video_url = self.link_input.text()
        if not YouTubeClient.is_valid_link(youtube_video_url):
            self.error("Invalid youtube link")
            return

        language = LANGUAGES[self.language_field.currentText()]
        note_type = self.note_type_field.currentText()
        text_field = self.text_field.currentText()
        audio_field = self.audio_field.currentText()
        picture_field = self.picture_field.currentText()

        if len(set([text_field, audio_field, picture_field])) != 3:
            self.error("All 3 fields must be different")
            return

        fallback = self.fallback_checkbox.isChecked()
        optimize_by_punctuation = self.optimize_checkbox.isChecked()
        dimensions = f"{self.width_input.value()}x{self.height_input.value()}"
        limit = self.limit_input.value()

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
        self.worker_ui = worker.create_deck(task=task)

    def read_settings(self):
        self.settings.beginGroup("MainWindow")
        self.link_input.setText(self.settings.value("video_url", ""))
        self.language_field.setCurrentText(
            self.settings.value("language_field", "English")
        )

        self.note_type_field.setCurrentText(self.settings.value("note_type_field", ""))
        self.audio_field.setCurrentText(self.settings.value("audio_field", ""))
        self.picture_field.setCurrentText(self.settings.value("picture_field", ""))
        self.text_field.setCurrentText(self.settings.value("text_field", ""))

        self.width_input.setValue(int(self.settings.value("width", 240)))
        self.height_input.setValue(int(self.settings.value("height", 160)))
        self.limit_input.setValue(int(self.settings.value("limit", 0)))

        self.fallback_checkbox.setChecked(
            string_to_bool(self.settings.value("fallback", False))
        )
        self.optimize_checkbox.setChecked(
            string_to_bool(self.settings.value("optimize_subtitles", False))
        )

        self.settings.endGroup()

    def write_settings(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("video_url", self.link_input.text())
        self.settings.setValue("language_field", self.language_field.currentText())

        self.settings.setValue("note_type_field", self.note_type_field.currentText())
        self.settings.setValue("audio_field", self.audio_field.currentText())
        self.settings.setValue("picture_field", self.picture_field.currentText())
        self.settings.setValue("text_field", self.text_field.currentText())

        self.settings.setValue("width", self.width_input.value())
        self.settings.setValue("height", self.height_input.value())
        self.settings.setValue("limit", self.limit_input.value())

        self.settings.setValue(
            "fallback", bool_to_string(self.fallback_checkbox.isChecked())
        )
        self.settings.setValue(
            "optimize_subtitles",
            bool_to_string(self.optimize_checkbox.isChecked()),
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
