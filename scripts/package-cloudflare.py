"""Build a Cloudflare Pages Direct Upload ZIP for the supplied production origin."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--origin', required=True, help='Actual production origin, e.g. https://my-project.pages.dev')
parser.add_argument('--output', type=Path, default=ROOT / '.artifacts' / 'cloudflare-pages.zip')
args = parser.parse_args()
parsed = urlsplit(args.origin)
if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
        or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
    parser.error('--origin must be an HTTPS origin without a path, credentials, query or fragment')
origin = args.origin.rstrip('/')
output = args.output.resolve()
output.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='daily-apps-cloudflare-') as temporary:
    stage = Path(temporary) / 'dist'
    stage.mkdir()
    for filename in ('style.css', 'app.js', 'favicon.svg', 'drive.jpg'):
        shutil.copy2(ROOT / 'dist' / filename, stage / filename)
    env = os.environ.copy()
    env.update(SITE_ORIGIN=origin, SITE_OUTPUT_DIR=str(stage))
    subprocess.run([sys.executable, str(ROOT / 'build.py')], env=env, check=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(stage).as_posix())
print(f'Created {output} for {origin}')
