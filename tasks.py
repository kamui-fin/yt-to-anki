import re
import invoke
from invoke import task
from pathlib import Path
from shutil import copytree


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


@task()
def anki(context):
    run_invoke_cmd(context, "anki")


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
def lint_black_diff(context):
    command = """
        poetry run black *.py ytsrs/ tests/unit/ --color 2>&1
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
        poetry run ruff *.py ytsrs/ tests/unit/ {argument_fix}
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
    print("Bundling the following packages:")
    tree = run_invoke_cmd(
        context, "poetry show --without dev --tree"
    ).stdout.splitlines()
    deps = [
        dep[re.search(r"[a-zA-Z0-9]", dep).start() :]
        .split()[0]
        .strip()
        .replace("-", "_")
        for dep in tree
    ]
    for dep in deps:
        dep_path = venv_location.joinpath(dep)
        copytree(dep_path, lib_location / dep)


@task()
def copy_source(context):
    copytree("ytsrs", "dist", dirs_exist_ok=True)


@task()
def bundle_ffmpeg(context):
    # assumes directory ffmpeg/ exists in current directory
    # moves ffmpeg.exe into dist/
    if not Path("dist/ffmpeg").exists():
        copytree("ffmpeg", "dist", dirs_exist_ok=True)


# before running: link to addons21 with `ln -s ./dist ~/.local/share/Anki2/addons21/yt2srs`
@task()
def package_dev(context):
    copy_source(context)
    bundle_libs(context)
    bundle_ffmpeg(context)

    # TODO: package into .ankiaddon
    #       filter out __pycache__


@task()
def dev(context):
    package_dev(context)
    anki(context)
