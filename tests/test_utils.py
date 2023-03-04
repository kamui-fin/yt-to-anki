from ytanki.client_youtube import YouTubeClient
from ytanki.utils import has_ffmpeg


def test_ffmpeg_does_not_exist():
    assert not has_ffmpeg("invalid_executable")


def test_yt_link_matching():
    assert not YouTubeClient.is_valid_link("https://doc.qt.io/qt-6")
    assert not YouTubeClient.is_valid_link("https://www.youtube.com/")
    assert not YouTubeClient.is_valid_link("https://www.youtube.com/@NoBoilerplate")
    assert not YouTubeClient.is_valid_link(
        "https://www.youtube.com/playlist?list=PLZaoyhMXgBzrbeVNhVz9_z8TvqyaOP963"
    )
    assert YouTubeClient.is_valid_link(
        "https://www.youtube.com/watch?v=glpR1MD1UoM&list=PLZaoyhMXgBzrbeVNhVz9_z8TvqyaOP963&index=1"
    )
    assert YouTubeClient.is_valid_link("https://www.youtube.com/watch?v=ifaLk5v3W90")
    assert YouTubeClient.is_valid_link("http://www.youtube.com/watch?v=ifaLk5v3W90")
    assert YouTubeClient.is_valid_link(
        "http://www.youtube.com/watch?v=ifaLk5v3W90&t=38s"
    )
    assert YouTubeClient.is_valid_link("https://youtu.be/JIvKgSyvtxI")
