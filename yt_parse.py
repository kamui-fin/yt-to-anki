import time
import datetime
from subprocess import call
import youtube_dl
import re, pathlib
# from PIL import Image
from glob import glob
import sys, os
from aqt import mw
from PyQt5 import QtCore, QtGui, QtWidgets
from aqt.utils import showInfo
from subprocess import check_output


home = os.path.dirname(os.path.abspath(__file__))
sub_dir = os.path.join(home, "subs")
vid_dir = os.path.join(home, "vid")


def parse_subs(filename):
	info = []
	text = pathlib.Path(filename).read_text(encoding="utf-8")
	chunked = re.split("\n\n", text)[1:]
	for chunk in chunked:
		try:
			start, end = re.findall("(\d+:\d+:\d+\.\d+) --> (\d+:\d+:\d+\.\d+)\n", chunk)[0]
		except IndexError:
			break #reached end of subs
		line = ''.join(chunk.split("\n")[1:])
		info.append([start, end, line])

	return info

def get_ffmpeg():
	op_s = os.name
	return os.path.join(home, "ffmpeg/ffmpeg.exe") if op_s == "nt" else "ffmpeg"


def crop_bottom(img, to_crop):
	pass
	# im = Image.open(img)
	# w, h = im.size
	# im.crop((0, 0, w, h - int(to_crop))).save(img)

class DlBar(QtWidgets.QDialog):

	def __init__(self):
		super().__init__()


	def setup_ui(self, **kwargs):
		self.resize(345, 70)
		self.progressBar = QtWidgets.QProgressBar(self)
		self.progressBar.setGeometry(QtCore.QRect(10, 20, 321, 23))
		self.progressBar.setWindowTitle("Downloading...")
		self.progressBar.setMinimum(0)
		self.progressBar.setMaximum(0)

		self.freqthread = DlThread(kwargs["link"], kwargs["lang"], kwargs["fallback"])
		self.freqthread.start()
		self.freqthread.done.connect(lambda : self.finish_up(**kwargs))
		self.show()

	def finish_up(self, **kwargs):
		self.close()
		subs_name, vid_name, title = self.freqthread.sources
		subs = parse_subs(subs_name)
		dial = GenBar()
		dial.setup_ui(subs, vid_name, title, **kwargs)

class DlThread(QtCore.QThread):
	done = QtCore.pyqtSignal(bool)

	def __init__(self, link, lang, fallback):
		super().__init__()
		self.link = link
		self.lang = lang
		self.fallback = fallback
		self.sources = ()

	def run(self):
		ydl_opts = {'subtitleslangs': [self.lang], "skip_download": True, "writesubtitles": True,
				"outtmpl": os.path.join(sub_dir, "%(title)s-%(id)s.%(ext)s"), "quiet":True, "no_warnings":True}

		opts_no_lang = {'subtitleslangs': [self.lang], "skip_download": True, "writeautomaticsub": True, "writesubtitles": True,
						"outtmpl": os.path.join(sub_dir, "%(title)s-%(id)s.%(ext)s"), "quiet":True, "no_warnings":True}

		vid_opts = {"outtmpl": os.path.join(vid_dir, "%(title)s-%(id)s.%(ext)s"), "quiet":True, "no_warnings":True} #

		ydl = youtube_dl.YoutubeDL(ydl_opts)
		ydl.download([self.link])
		if self.fallback:
			if not glob(sub_dir + "/*"):
				ydl = youtube_dl.YoutubeDL(opts_no_lang)
				ydl.download([self.link])

		ydl = youtube_dl.YoutubeDL(vid_opts)
		ydl.download([self.link])
		title = ydl.extract_info(self.link, download=False)["title"]
		dL_sources = (glob(sub_dir + "/*")[0], glob(vid_dir  + "/*")[0], title)
		self.sources = dL_sources
		self.done.emit(True)

class GenBar(QtWidgets.QDialog):

	def __init__(self):
		super().__init__()

	def setup_ui(self,subs, vid_name, title, **kwargs):
		self.resize(350, 77)
		self.label = QtWidgets.QLabel(self)
		self.label.setGeometry(QtCore.QRect(140, 20, 75, 13))
		self.progressBar = QtWidgets.QProgressBar(self)
		self.progressBar.setGeometry(QtCore.QRect(10, 40, 330, 23))
		self.setWindowTitle("Adding cards")
		self.label.setText("Generating")
		self.threadClass = GenThread(subs, vid_name, title,kwargs["output_dir"], kwargs["limit"], kwargs["dim"], kwargs["crop"], kwargs["note_type"], kwargs["text_field"], kwargs["audio_field"], kwargs["pic_field"])
		self.threadClass.start()
		self.threadClass.updateNum.connect(self.updateProgress)
		self.threadClass.addToDeckSignal.connect(self.add_card)
		self.threadClass.finished.connect(lambda: self.close())
		self.threadClass.finishTime.connect(self.showTime)
		self.show()

	def updateProgress(self,val):
		self.progressBar.setValue(val)

	def showTime(self, duration):
		showInfo(f"Generated all cards in {str(duration)} seconds")

	@QtCore.pyqtSlot(str, str, str, str, str, str,  str, str)
	def add_card(self,text, raudio, rpic , title, note_type, text_field, audio_field, pic_field):
		deckId = mw.col.decks.id(title)
		mw.col.decks.select(deckId)
		basic_model = mw.col.models.byName(note_type)
		basic_model['did'] = deckId
		mw.col.models.save(basic_model)
		mw.col.models.setCurrent(basic_model)
		senCard = mw.col.newNote()
		senCard[text_field] = text

		# Audio
		audiofname = mw.col.media.addFile(raudio)
		ankiaudiofname = u'[sound:%s]' % audiofname
		senCard[audio_field] = ankiaudiofname

		# Picture
		picfname = mw.col.media.addFile(rpic)
		ankipicname = u'<img src="%s">' % picfname
		senCard[pic_field] = ankipicname

		# if tag:
		#     senCard.addTag(os.path.basename(video).split(".")[0])

		mw.col.addNote(senCard)
		mw.col.save()

	def closeEvent(self, event):
		self.threadClass.stop()
		super(GenBar, self).closeEvent(event)

class GenThread(QtCore.QThread):
	updateNum = QtCore.pyqtSignal(int)
	finished = QtCore.pyqtSignal(bool)
	finishTime = QtCore.pyqtSignal(float)
	addToDeckSignal = QtCore.pyqtSignal(str, str, str, str, str, str, str, str)

	def __init__(self,info, video, vid_title, output_dir, limit, dim,
							crop, note_type, text_field, audio_field, pic_field):
		self.info = info
		self.video = video
		self.vid_title =vid_title
		self.output_dir = output_dir
		self.limit = limit
		self.dim = dim
		self.crop = crop
		self.note_type = note_type
		self.text_field = text_field
		self.audio_field = audio_field
		self.pic_field = pic_field
		self.stop_flag = False
		super().__init__()

	def stop(self):
		self.stop_flag = True

	def run(self):

		ffmpeg = get_ffmpeg()
		info = self.info[:self.limit] if self.limit else self.info
		count = 0
		total_subs = len(info)
		timer_start = time.perf_counter()
		for sub in info:
			if self.stop_flag:
				os.remove(self.video)
				sub_file = glob(sub_dir + "/*")[0]
				os.remove(sub_file)
				return
			start, end, text = sub
			startTime = datetime.datetime.strptime(start, "%H:%M:%S.%f")
			endTime = datetime.datetime.strptime(end, "%H:%M:%S.%f")
			diff = endTime - startTime

			#audio
			a_name = os.path.join(self.output_dir, f"{self.vid_title}_{str(start).replace('.','_').replace(':','_')}_{str(diff.total_seconds()).replace('.','_').replace(':','_')}.mp3")
			command = ffmpeg + ' -ss ' + str(startTime.time()) + ' -i ' + '"' + self.video + '"' + ' -t 00:' + str(
				diff.total_seconds())  + " -loglevel quiet" + ' "' + a_name + '"'

			try:
				output = check_output(command, shell=True)
			except:
				continue

			#pic
			p_name = os.path.join(self.output_dir, f"{self.vid_title}_{str(start).replace('.','_').replace(':','_')}.jpeg")
			command = ffmpeg + ' -ss ' + str(
				startTime.time()) + ' -i ' + '"' + self.video + '" ' + '-s ' + self.dim + ' -vframes 1 -q:v 2 ' + "-loglevel quiet " + '"' + p_name + '"' # + '-loglevel quiet '

			try:
				output = check_output(command, shell=True)
			except:
				continue

			if self.crop:
				crop_bottom(p_name, self.crop)

			sub.extend([a_name, p_name])
			count += 1
			percent = (count / total_subs) * 100
			self.updateNum.emit(percent)

			*_, text, raudio, rpic = sub
			self.addToDeckSignal.emit( text, raudio, rpic, self.vid_title,  self.note_type, self.text_field, self.audio_field, self.pic_field)

		timer_end = time.perf_counter()
		finishedtime = timer_end - timer_start
		os.remove(self.video)
		sub_file = glob(sub_dir + "/*")[0]
		os.remove(sub_file)
		self.finished.emit(True)
		self.finishTime.emit(finishedtime)

def create_subs2srs_deck(**kwargs):
	dl_bar = DlBar()
	dl_bar.setup_ui(**kwargs)
