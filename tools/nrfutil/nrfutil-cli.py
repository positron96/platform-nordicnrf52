import sys
import site
import os
import subprocess as sp

SELF_DIR = os.path.dirname(os.path.abspath(__file__))

def install_python_deps():
    python_deps_dir = os.path.normpath(
        os.path.join(
            SELF_DIR,
            "site-packages",
            "python%d.%d" % (sys.version_info[0], sys.version_info[1]),
        )
    )

    if not os.path.isdir(python_deps_dir):
        print("Installing Python dependencies...")
        pipinstall = [
            os.environ.get("PYTHONEXEPATH", os.path.normpath(sys.executable)),
            "-m", "pip",
            "install", "--target",  python_deps_dir]

        sp.check_call(pipinstall + [
            '--ignore-requires-python',
            '--only-binary=:all:',
            '--python-version=3.10',
            'pc_ble_driver_py==0.17'])

        sp.check_call(pipinstall + [
            "--ignore-installed",
            "--ignore-requires-python",
            '-r', os.path.join(SELF_DIR, 'requirements.txt')])

    return python_deps_dir


try:
    python_deps_dir = install_python_deps()
except sp.CalledProcessError as e:
    print('Error installing dependencies')
    sys.exit(1)

site.addsitedir(python_deps_dir)
sys.path.insert(0, python_deps_dir)

from nordicsemi.__main__ import cli

if __name__ == "__main__":
    cli()
