from PyQt5 import QtCore, QtWidgets
from ui import Window
from constants import *
import json
import sys, os
import yt_parse
from aqt import mw
from aqt.utils import showInfo



class MW(Window):

	def __init__(self):
		super().__init__()

	def setup_ui(self):
		self.config = {}
		self.col = mw.col
		notes = self.col.models.allNames()
		fields = self.get_fields()
		notes.insert(0,"")
		fields.insert(0,"")

		self.subs_lang_box.addItems(lang_list)
		self.note_box.addItems(notes)
		self.audio_box.addItems(fields)
		self.pic_box.addItems(fields)
		self.text_box.addItems(fields)

		self.choose_dir_button.clicked.connect(self.choose_dir)
		self.generate_button.clicked.connect(lambda : self.generate())

	def choose_dir(self):
		directory = str(QtWidgets.QFileDialog.getExistingDirectory(self,"Output Folder"))
		self.output_box.setText(directory)

	def get_fields(self):
		modeljson = self.col.db.all("select models from col")[0][0]
		pyjson = json.loads(modeljson)
		fields = [""]

		for key in pyjson.keys():
			for i in pyjson[key]["flds"]:
				fields.append(pyjson[key]["name"] + ": " + i["name"])

		return fields

	def generate(self):
		self.config["link"] = str(self.link_box.text())
		try:
			self.config["lang"] = {v:k for k, v in LANGUAGES.items()}[str(self.subs_lang_box.currentText())]
		except KeyError:
			self.error("Please enter a language")
			return
		self.config["fallback"] = bool(self.fallback_check.isChecked())
		self.config["dim"] = f"{self.width_box.value()}x{self.height_box.value()}"
		self.config["crop"] = self.crop_bottom_box.value()
		self.config["limit"] = self.limit_box.value()
		self.config["col"] = self.col
		self.config["output_dir"] = str(self.output_box.text())
		self.config["note_type"] = str(self.note_box.currentText())
		self.config["text_field"] = str(self.text_box.currentText()).split(": ")[-1]
		self.config["audio_field"] = str(self.audio_box.currentText()).split(": ")[-1]
		self.config["pic_field"] = str(self.pic_box.currentText()).split(": ")[-1]

		#check
		if not self.config["pic_field"] or not self.config["audio_field"] or not self.config["text_field"]:
			self.error("Please enter all fields")
			return
		if not self.config["note_type"]:
			self.error("Please choose a note type")
			return
		if not self.config["link"].startswith("https://www.youtube.com/watch?v="):
			self.error("Invalid youtube link")
			return

		if self.config["crop"] > int(self.config["dim"].split("x")[0]):
			self.error("Invalid crop value")
			return

		if not os.path.isdir(self.config["output_dir"]):
			self.error("Invalid output folder")
			return

		if sys.platform.startswith("linux"):
			self.error("Linux is not a supported os")
			return


		yt_parse.create_subs2srs_deck(**self.config)


	def error(self, text,title="Error has occured"):
		dialog = QtWidgets.QMessageBox()
		dialog.setWindowTitle(title)
		dialog.setText(text)
		dialog.setIcon(QtWidgets.QMessageBox.Warning)
		dialog.exec_()


def launch():
	screen = MW()
	screen.setup_ui()
	screen.show()
