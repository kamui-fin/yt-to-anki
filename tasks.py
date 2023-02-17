import re
import invoke
from invoke import task
from pathlib import Path
from shutil import copytree
from markdown import markdown


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
def lint_mypy(context):
    # Need to delete the cache every time because otherwise mypy gets
    # stuck with 0 warnings very often.
    run_invoke_cmd(
        context,
        """
        poetry run mypy ytanki tests
            --show-error-codes
            --disable-error-code=arg-type
            --disable-error-code=attr-defined
            --disable-error-code=import
            --disable-error-code=misc
            --disable-error-code=no-any-return
            --disable-error-code=no-redef
            --disable-error-code=no-untyped-call
            --disable-error-code=no-untyped-def
            --disable-error-code=operator
            --disable-error-code=type-arg
            --disable-error-code=var-annotated
            --disable-error-code=union-attr
            --strict
        """,
    )


@task
def lint_black_diff(context):
    command = """
        poetry run black *.py ytanki/ tests/unit/ --color 2>&1
    """
    result = run_invoke_cmd(context, command)

    # black always exits with 0, so we handle the output.
    if "reformatted" in result.stdout:
        print("invoke: black found issues")  # noqa: T201
        result.exited = 1
        raise invoke.exceptions.UnexpectedExit(result)


@task
def lint_ruff(context, fix=False):
    argument_fix = "--fix" if fix else ""
    command = f"""
        poetry run ruff *.py ytanki/ tests/unit/ {argument_fix}
    """
    run_invoke_cmd(context, command)


@task()
def lint(context):
    lint_black_diff(context)
    lint_ruff(context)


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
def copy_source(context):
    copytree("ytanki", "dist", dirs_exist_ok=True)


@task()
def bundle_ffmpeg(context):
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
    run_invoke_cmd(context, "zip -r ytanki.ankiaddon dist/*")


def readme_to_html():
    Path("README.html").write_text(markdown(Path("README.md").read_text()))


@task()
def compile_ui(context):
    run_invoke_cmd(context, "poetry run pyuic5 -x ytanki/gui.ui -o ytanki/gui.py")


@task()
def package(context):
    readme_to_html()
    package_dev(context)
    remove_pycache()
    compress(context)


@task()
def dev(context):
    package_dev(context)
    anki(context)
