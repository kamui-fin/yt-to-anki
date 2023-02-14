import os

from anki.collection import Collection
from aqt import mw
from PyQt5 import QtWidgets
from aqt.utils import showCritical

from . import worker
from .constants import LANGUAGES, lang_list
from .models import FieldsConfiguration, GenerateVideoTask
from .ui import Window
from .utils import has_ffmpeg


class MW(Window):
    def __init__(self):
        super().__init__()

    def setup_ui(self):
        self.col = mw.col
        notes = self.col.models.allNames()
        fields = self.get_fields()
        notes.insert(0, "")
        fields.insert(0, "")

        self.subs_lang_box.addItems(lang_list)
        self.note_box.addItems(notes)
        self.audio_box.addItems(fields)
        self.pic_box.addItems(fields)
        self.text_box.addItems(fields)

        self.choose_dir_button.clicked.connect(self.choose_dir)
        self.generate_button.clicked.connect(lambda: self.generate())

    def choose_dir(self):
        directory = str(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Output Folder")
        )
        self.output_box.setText(directory)

    def get_fields(self):
        fields_res = self.col.db.all(
            "SELECT notetypes.name, FIELDS.name FROM FIELDS INNER JOIN notetypes ON FIELDS.ntid = notetypes.id"  # noqa: E501
        )
        fields = []

        for entry in fields_res:
            fld = f"{entry[0]}: {entry[1]}"
            fields.append(fld)

        return fields

    def generate(self):
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

        collection: Collection = self.col
        fallback: bool = bool(self.fallback_check.isChecked())
        dimensions: str = f"{self.width_box.value()}x{self.height_box.value()}"
        limit: int = self.limit_box.value()

        output_dir: str = str(self.output_box.text())
        if not os.path.isdir(output_dir):
            self.error("Invalid output folder")
            return

        note_type: str = str(self.note_box.currentText())
        if len(note_type) == 0:
            self.error("Please choose a note type")
            return

        text_field: str = str(self.text_box.currentText()).split(": ")[-1]
        audio_field: str = str(self.audio_box.currentText()).split(": ")[-1]
        picture_field: str = str(self.pic_box.currentText()).split(": ")[-1]

        if len(text_field) == 0 or len(audio_field) == 0 or len(picture_field) == 0:
            self.error("Please enter all fields")
            return

        fields: FieldsConfiguration = FieldsConfiguration(
            note_type=note_type,
            text_field=text_field,
            audio_field=audio_field,
            picture_field=picture_field,
        )
        task = GenerateVideoTask(
            youtube_video_url=youtube_video_url,
            language=language,
            fallback=fallback,
            dimensions=dimensions,
            limit=limit,
            collection=collection,
            output_dir=output_dir,
            fields=fields,
        )
        worker.create_subs2srs_deck(task=task)

    @staticmethod
    def error(text, title="Error has occured"):
        dialog = QtWidgets.QMessageBox()
        dialog.setWindowTitle(title)
        dialog.setText(text)
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        dialog.exec_()


def launch():
    screen = MW()
    screen.setup_ui()
    if not has_ffmpeg():
        showCritical("Linux or Mac users must install ffmpeg to PATH.")
    else:
        screen.show()
