import sys
from os.path import dirname, join

if "pytest" not in sys.modules:
    sys.path.append(join(dirname(__file__), "lib"))

    from aqt import mw
    from aqt.qt import QAction
    from .main import launch

    action = QAction("YouTube to Anki", mw)
    action.triggered.connect(launch)
    mw.form.menuTools.addAction(action)
