import os, sys

home = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,home)

from aqt import mw
from aqt.qt import *
from yt_main import launch


action = QAction("YT Subs2Srs", mw)
action.triggered.connect(launch)
mw.form.menuTools.addAction(action)
