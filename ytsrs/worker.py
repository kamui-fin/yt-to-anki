import datetime
import os
import time
from subprocess import check_output
from typing import List, Optional

from aqt import mw
from aqt.utils import showInfo
from PyQt5 import QtCore, QtWidgets

from .client_youtube import SubtitleRange, YouTubeClient, YouTubeDownloadResult
from .models import FieldsConfiguration, GenerateVideoTask


def get_ffmpeg():
    home = os.path.dirname(os.path.abspath(__file__))
    op_s = os.name
    return os.path.join(home, "ffmpeg/ffmpeg.exe") if op_s == "nt" else "ffmpeg"


class DlBar(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

    def setup_ui(self, *, task: GenerateVideoTask):
        self.resize(345, 70)
        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setGeometry(QtCore.QRect(10, 20, 321, 23))
        self.progressBar.setWindowTitle("Downloading...")
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)

        self.freqthread = DlThread(task=task)
        self.freqthread.start()
        self.freqthread.done.connect(lambda: self.finish_up(task=task))
        self.show()

    def finish_up(self, *, task):
        self.close()
        youtube_download_result: YouTubeDownloadResult = self.freqthread.sources
        dial = GenBar()
        dial.setup_ui(task, youtube_download_result)


class DlThread(QtCore.QThread):
    done = QtCore.pyqtSignal(bool)

    def __init__(self, *, task: GenerateVideoTask):
        super().__init__()
        self.task: GenerateVideoTask = task
        self.sources: Optional[YouTubeDownloadResult] = None

    def run(self):
        result: YouTubeDownloadResult = YouTubeClient.download_video_files(self.task)
        self.sources = result
        self.done.emit(True)


class GenBar(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

    def setup_ui(
        self, task: GenerateVideoTask, youtube_download_result: YouTubeDownloadResult
    ):
        self.resize(350, 77)
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(140, 20, 75, 13))
        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setGeometry(QtCore.QRect(10, 40, 330, 23))
        self.setWindowTitle("Adding cards")
        self.label.setText("Generating")
        self.threadClass = GenThread(
            task=task,
            youtube_download_result=youtube_download_result,
        )
        self.threadClass.start()
        self.threadClass.updateNum.connect(self.updateProgress)
        self.threadClass.addToDeckSignal.connect(self.add_card)
        self.threadClass.finished.connect(lambda: self.close())
        self.threadClass.finishTime.connect(self.showTime)
        self.show()

    def updateProgress(self, val):
        self.progressBar.setValue(val)

    def showTime(self, duration):
        showInfo(f"Generated all cards in {str(duration)} seconds")

    @QtCore.pyqtSlot(SubtitleRange, str, FieldsConfiguration)
    def add_card(
        self,
        subtitle_range: SubtitleRange,
        title: str,
        fields: FieldsConfiguration,
    ):
        deckId = mw.col.decks.id(title)
        mw.col.decks.select(deckId)
        basic_model = mw.col.models.byName(fields.note_type)
        basic_model["did"] = deckId
        mw.col.models.save(basic_model)
        mw.col.models.setCurrent(basic_model)
        senCard = mw.col.newNote()
        senCard[fields.text_field] = subtitle_range.text

        # Audio
        audiofname = mw.col.media.addFile(subtitle_range.path_to_audio)
        ankiaudiofname = "[sound:%s]" % audiofname
        senCard[fields.audio_field] = ankiaudiofname

        # Picture
        picfname = mw.col.media.addFile(subtitle_range.path_to_picture)
        ankipicname = '<img src="%s">' % picfname
        senCard[fields.picture_field] = ankipicname

        mw.col.addNote(senCard)
        mw.col.save()

    def closeEvent(self, event):
        self.threadClass.stop()
        super(GenBar, self).closeEvent(event)


class GenThread(QtCore.QThread):
    updateNum = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(bool)
    finishTime = QtCore.pyqtSignal(float)
    addToDeckSignal = QtCore.pyqtSignal(SubtitleRange, str, FieldsConfiguration)

    def __init__(
        self,
        task: GenerateVideoTask,
        youtube_download_result: YouTubeDownloadResult,
    ):
        self.task: GenerateVideoTask = task
        self.youtube_download_result: YouTubeDownloadResult = youtube_download_result

        self.stop_flag = False
        super().__init__()

    def stop(self):
        self.stop_flag = True

    def run(self):
        limit = self.task.limit

        ffmpeg = get_ffmpeg()
        info: List[SubtitleRange] = self.youtube_download_result.subtitles[:limit]
        count = 0
        total_subs = len(info)
        timer_start = time.perf_counter()

        for sub in info:
            if self.stop_flag:
                os.remove(self.youtube_download_result.path_to_video)
                os.remove(self.youtube_download_result.path_to_subtitles_file)
                return

            startTime = datetime.datetime.strptime(sub.time_start, "%H:%M:%S.%f")
            endTime = datetime.datetime.strptime(sub.time_end, "%H:%M:%S.%f")
            diff = endTime - startTime

            a_name = os.path.join(
                self.task.output_dir,
                f"{self.youtube_download_result.video_title}_{str(sub.time_start).replace('.','_').replace(':','_')}_{str(diff.total_seconds()).replace('.','_').replace(':','_')}.mp3",
            )
            command = (
                ffmpeg
                + " -y "  # Overwrite output file.
                + " -ss "
                + str(startTime.time())
                + " -i "
                + '"'
                + self.youtube_download_result.path_to_video
                + '"'
                + " -t 00:"
                + str(diff.total_seconds())
                + " -loglevel quiet"
                + ' "'
                + a_name
                + '"'
            )

            try:
                check_output(command, shell=True)
            except:  # noqa: E722 # FIXME: Do not use bare `except`
                continue

            p_name = os.path.join(
                self.task.output_dir,
                f"{self.youtube_download_result.video_title}_{str(sub.time_start).replace('.','_').replace(':','_')}.jpeg",
            )
            command = (
                ffmpeg
                + " -y "  # Overwrite output file.
                + " -ss "
                + str(startTime.time())
                + " -i "
                + '"'
                + self.youtube_download_result.path_to_video
                + '" '
                + "-s "
                + self.task.dimensions
                + " -vframes 1 -q:v 2 "
                + "-loglevel quiet "
                + '"'
                + p_name
                + '"'
            )

            try:
                check_output(command, shell=True)
            except:  # noqa: E722 # FIXME: Do not use bare `except`
                continue

            sub.add_paths_to_picture_and_audio(
                path_to_picture=p_name, path_to_audio=a_name
            )

            count += 1
            percent = (count / total_subs) * 100
            self.updateNum.emit(percent)

            self.addToDeckSignal.emit(
                sub,
                self.youtube_download_result.video_title,
                self.task.fields,
            )

        timer_end = time.perf_counter()
        finishedtime = timer_end - timer_start

        os.remove(self.youtube_download_result.path_to_video)
        os.remove(self.youtube_download_result.path_to_subtitles_file)

        self.finished.emit(True)
        self.finishTime.emit(finishedtime)


def create_subs2srs_deck(*, task: GenerateVideoTask):
    dl_bar = DlBar()
    dl_bar.setup_ui(task=task)
