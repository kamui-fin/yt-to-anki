import os
import re
import time
from typing import List, Optional

from PyQt5.QtCore import Qt
from aqt import mw
from aqt.utils import showCritical, showInfo
from PyQt5 import QtCore, QtWidgets


from .errors import NoSubtitlesException
from .client_youtube import SubtitleRange, YouTubeClient, YouTubeDownloadResult
from .models import FieldsConfiguration, GenerateVideoTask
from .utils import with_limit
from .ffmpeg import Ffmpeg


class ProgressBarDialog(QtWidgets.QDialog):
    def __init__(self, window_title, progress_label):
        super().__init__()
        self.resize(350, 77)
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(0, 20, self.width(), 13))
        self.label.setAlignment(Qt.AlignCenter)
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setGeometry(QtCore.QRect(10, 40, 330, 23))
        self.setWindowTitle(window_title)
        self.label.setText(progress_label)
        self.progress_bar.setValue(0)


class DownloadYouTubeVideoBar(ProgressBarDialog):
    def __init__(self):
        super().__init__("Downloading...", "Downloading video and subtitles...")

    def setup_ui(self, *, task: GenerateVideoTask):
        self.download_thread = DownloadYouTubeVideoThread(task=task)
        self.download_thread.on_progress.connect(lambda d: self.on_youtube_progress(d))
        self.download_thread.done.connect(lambda: self.finish_up(task=task))
        self.download_thread.is_error.connect(lambda: self.show_error())
        self.download_thread.start()
        self.show()

    def on_youtube_progress(self, d: dict):
        if d["status"] == "downloading":
            ascii_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
            p = ascii_escape.sub("", d["_percent_str"]).strip().replace("%", "")
            self.progress_bar.setValue(int(float(p)))
        elif d["status"] == "finished":
            self.progress_bar.setValue(100)

    def show_error(self):
        self.close()
        msg = self.download_thread.error_message
        showCritical(msg)

    def finish_up(self, *, task):
        self.close()
        youtube_download_result = self.download_thread.sources
        if youtube_download_result:
            dial = GenerateCardsBar()
            dial.setup_ui(task, youtube_download_result)


class DownloadYouTubeVideoThread(QtCore.QThread):
    done = QtCore.pyqtSignal(bool)
    is_error = QtCore.pyqtSignal(bool)
    on_progress = QtCore.pyqtSignal(dict)

    def __init__(self, *, task: GenerateVideoTask):
        super().__init__()
        self.task: GenerateVideoTask = task
        self.error_message: str = ""
        self.sources: Optional[YouTubeDownloadResult] = None

    def run(self):
        try:
            result: YouTubeDownloadResult = YouTubeClient.download_video_files(
                self.task, lambda p: self.on_progress.emit(p)
            )
            self.sources = result
            self.done.emit(True)
        except NoSubtitlesException:
            self.is_error.emit(True)
            self.error_message = (
                "Man-made subtitles could not be found. Consider enabling fallback."
            )


class GenerateCardsBar(ProgressBarDialog):
    def __init__(self):
        super().__init__("Adding cards...", "Generating cards..")

    def setup_ui(
        self, task: GenerateVideoTask, youtube_download_result: YouTubeDownloadResult
    ):
        self.thread_class = GenerateCardsThread(
            task=task,
            youtube_download_result=youtube_download_result,
        )
        self.thread_class.update_num.connect(self.updateProgress)
        self.thread_class.add_to_deck_signal.connect(self.add_card)
        self.thread_class.finished.connect(self.close)
        self.thread_class.finish_time.connect(self.showTime)
        self.thread_class.start()
        self.show()

    def updateProgress(self, val):
        self.progress_bar.setValue(val)

    def showTime(self, duration, total_cards):
        showInfo(f"Generated {total_cards} cards in {str(round(duration, 1))} seconds")

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
        self.thread_class.stop()
        super(GenerateCardsBar, self).closeEvent(event)


class GenerateCardsThread(QtCore.QThread):
    update_num = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(bool)
    finish_time = QtCore.pyqtSignal(float, int)
    add_to_deck_signal = QtCore.pyqtSignal(SubtitleRange, str, FieldsConfiguration)

    def __init__(
        self,
        task: GenerateVideoTask,
        youtube_download_result: YouTubeDownloadResult,
    ):
        super().__init__()
        self.task: GenerateVideoTask = task
        self.youtube_download_result: YouTubeDownloadResult = youtube_download_result
        self.stop_flag = False

    def stop(self):
        self.stop_flag = True

    def clean_up(self):
        os.remove(self.youtube_download_result.path_to_video)
        os.remove(self.youtube_download_result.path_to_subtitles_file)

    def run(self):
        count = 0
        timer_start = time.perf_counter()
        subtitles: List[SubtitleRange] = with_limit(
            self.youtube_download_result.subtitles, self.task.limit
        )
        for subtitle in subtitles:
            if self.stop_flag:
                return self.clean_up()

            ffmpeg = Ffmpeg(
                self.task.output_dir,
                subtitle,
                self.youtube_download_result.path_to_video,
                self.youtube_download_result.video_title,
            )
            try:
                ffmpeg.generate_media(self.task.dimensions)
            except:  # noqa: E722 # FIXME: Do not use bare `except`
                continue

            count += 1
            percent = int((count / len(subtitles)) * 100)
            self.update_num.emit(percent)

            self.add_to_deck_signal.emit(
                subtitle,
                self.youtube_download_result.video_title,
                self.task.fields,
            )

        timer_end = time.perf_counter()
        finished_time = timer_end - timer_start

        self.clean_up()

        self.finished.emit(True)
        self.finish_time.emit(finished_time, len(subtitles))


def create_deck(*, task: GenerateVideoTask):
    dl_bar = DownloadYouTubeVideoBar()
    dl_bar.setup_ui(task=task)
