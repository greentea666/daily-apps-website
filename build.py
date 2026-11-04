"""Compatibility entry point. The website is built with JavaScript and React."""
from pathlib import Path
import subprocess

subprocess.run(['node', 'scripts/build.mjs'], cwd=Path(__file__).resolve().parent, check=True)
