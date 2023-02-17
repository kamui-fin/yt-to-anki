import re
import invoke
from invoke import task
from pathlib import Path
from shutil import copytree
from markdown2 import markdown


def one_line_command(string):
    return re.sub("\\s+", " ", string).strip()


def run_invoke_cmd(context, cmd) -> invoke.runners.Result:
    return context.run(
        one_line_command(cmd),
        env=None,
        hide=False,
        warn=False,
        pty=False,
        echo=True,
    )


@task
def test_unit(context):
    run_invoke_cmd(
        context,
        """
        poetry run coverage run
            --rcfile=.coveragerc
            --branch
            -m pytest tests/unit/
        """,
    )


@task
def format_black(context):
    command = """
        poetry run black *.py ytanki/ tests/unit/ --color 2>&1
    """
    result = run_invoke_cmd(context, command)

    # black always exits with 0, so we handle the output.
    if "reformatted" in result.stdout:
        print("invoke: black found issues")
        result.exited = 1
        raise invoke.exceptions.UnexpectedExit(result)


@task
def lint_pyright(context):
    run_invoke_cmd(context, "poetry run pyright")


@task()
def lint(context):
    format_black(context)
    lint_pyright(context)


@task()
def test(context):
    test_unit(context)


@task()
def check(context):
    lint(context)
    test(context)


@task()
def bundle_libs(context):
    lib_location = Path("./dist/lib")
    if lib_location.exists():
        # avoid rebundling
        return

    lib_location.mkdir()
    print("Finding venv location:")
    venv_location = (
        Path(run_invoke_cmd(context, "poetry env info -p").stdout.strip())
        / "lib"
        / "python3.10"  # TODO: dynamically find this directory
        / "site-packages"
    )
    deps = ["webvtt", "yt_dlp"]
    for dep in deps:
        dep_path = venv_location.joinpath(dep)
        if dep_path.exists():
            copytree(dep_path, lib_location / dep)


@task()
def copy_source(_):
    copytree("ytanki", "dist", dirs_exist_ok=True)


@task()
def bundle_ffmpeg(_):
    # assumes directory ffmpeg/ exists in current directory
    # moves ffmpeg.exe into dist/
    if not Path("dist/ffmpeg").exists() and Path("ffmpeg").exists():
        copytree("ffmpeg", "dist", dirs_exist_ok=True)


@task()
def anki(context):
    run_invoke_cmd(context, "anki")


def remove_pycache():
    [p.unlink() for p in Path(".").rglob("*.py[co]")]
    [p.rmdir() for p in Path(".").rglob("__pycache__")]


@task()
def package_dev(context):
    compile_ui(context)
    copy_source(context)
    bundle_libs(context)
    bundle_ffmpeg(context)


@task()
def compress(context):
    run_invoke_cmd(context, "(cd dist && zip -r $OLDPWD/ytanki.ankiaddon .)")


# Credit to https://github.com/luoliyan/chinese-support-redux/blob/master/convert-readme.py
@task
def readme_to_html(context):
    """Covert GitHub mardown to AnkiWeb HTML."""
    # permitted tags: img, a, b, i, code, ul, ol, li

    translate = [
        (r"<h1>([^<]+)</h1>", r""),
        (r"<h2>([^<]+)</h2>", r"<b><i>\1</i></b>\n\n"),
        (r"<h3>([^<]+)</h3>", r"<b>\1</b>\n\n"),
        (r"<strong>([^<]+)</strong>", r"<b>\1</b>"),
        (r"<em>([^<]+)</em>", r"<i>\1</i>"),
        (r"<kbd>([^<]+)</kbd>", r"<code><b>\1</b></code>"),
        (r"</a></p>", r"</a></p>\n"),
        (r"<p>", r""),
        (r"</p>", r"\n\n"),
        (r"</(ol|ul)>(?!</(li|[ou]l)>)", r"</\1>\n"),
    ]

    with open("README.md", encoding="utf-8") as f:
        html = "".join(filter(None, markdown(f.read()).split("\n")))

    for a, b in translate:
        html = re.sub(a, b, html)

    with open("README.html", "w", encoding="utf-8") as f:
        f.write(html.strip())


@task()
def compile_ui(context):
    run_invoke_cmd(context, "poetry run pyuic5 -x ytanki/gui.ui -o ytanki/gui.py")


@task()
def package(context):
    readme_to_html(context)
    package_dev(context)
    remove_pycache()
    compress(context)


@task()
def dev(context):
    package_dev(context)
    anki(context)
