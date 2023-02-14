from ytsrs.utils import has_ffmpeg


def test_ffmpeg_does_not_exist():
    assert not has_ffmpeg("invalid_executable")
