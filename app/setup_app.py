"""py2app build for Miotła.app.

Alias build (fast, references this repo/venv):
    .venv/bin/python setup_app.py py2app -A
Output: dist/Miotła.app
"""
from setuptools import setup

OPTIONS = {
    "iconfile": "miotla_app/assets/app_icon.icns",
    "plist": {
        "CFBundleName": "Miotła",
        "CFBundleDisplayName": "Miotła",
        "CFBundleIdentifier": "com.miotla.app",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "LSMinimumSystemVersion": "11.0",
        "NSHighResolutionCapable": True,
        "LSMultipleInstancesProhibited": True,
    },
    "packages": ["miotla_app"],
}

setup(
    app=["miotla_launch.py"],
    name="Miotła",
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
