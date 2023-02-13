import re

import invoke
from invoke import task


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
        coverage run
            --rcfile=.coveragerc
            --branch
            -m pytest
            tests/unit/
        """,
    )


@task
def lint_black_diff(context):
    command = """
        black *.py --color 2>&1
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
        ruff *.py {argument_fix}
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
