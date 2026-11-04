"""Build a reproducible Cloudflare Pages Direct Upload ZIP for a production origin."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]

def production_origin(value):
    """Reject URL components that cannot describe a canonical website origin."""
    try:
        parsed = urlsplit(value)
        # Accessing port rejects malformed and out-of-range port numbers.
        port = parsed.port
        if (any(char.isspace() or ord(char) < 32 for char in value)
                or parsed.scheme != 'https' or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.path not in ('', '/') or parsed.query or parsed.fragment
                or '\\' in value or port == 0):
            raise ValueError
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            'must be an HTTPS origin without credentials, path, whitespace, query or fragment'
        ) from error
    return value.rstrip('/')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', required=True, type=production_origin,
                        help='Actual production origin, e.g. https://my-project.pages.dev')
    parser.add_argument('--output', type=Path,
                        default=ROOT / '.artifacts' / 'cloudflare-pages.zip')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.suffix.lower() != '.zip':
        parser.error('--output must have a .zip extension')
    protected = ('dist', 'public', 'src', 'scripts', 'node_modules')
    if any(output == ROOT / directory or ROOT / directory in output.parents
           for directory in protected):
        parser.error('--output must be outside website source and generated dist directories')
    if output.exists() and not output.is_file():
        parser.error('--output must name a file')

    # The builder owns all assets. An isolated stage avoids changing a local
    # preview or shipping files left over from an earlier build.
    with tempfile.TemporaryDirectory(prefix='daily-apps-cloudflare-') as temporary:
        stage = Path(temporary) / 'dist'
        env = os.environ.copy()
        # This command creates a production upload. A preview-only setting in
        # the caller's shell must not silently block the published site in search.
        env.update(SITE_ORIGIN=args.origin, SITE_OUTPUT_DIR=str(stage), SITE_NOINDEX='0')
        subprocess.run(['node', str(ROOT / 'scripts' / 'build.mjs')],
                       cwd=ROOT, env=env, check=True)
        if not (stage / 'index.html').is_file():
            raise RuntimeError('Build did not generate index.html')
        output.parent.mkdir(parents=True, exist_ok=True)
        archive_path = None
        try:
            with tempfile.NamedTemporaryFile(prefix='.cloudflare-', suffix='.zip',
                                             dir=output.parent, delete=False) as handle:
                archive_path = Path(handle.name)
            with ZipFile(archive_path, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
                for path in sorted(stage.rglob('*')):
                    if path.is_symlink():
                        raise ValueError(f'Build contains a symbolic link: {path.relative_to(stage)}')
                    if not path.is_file():
                        continue
                    # Fixed dates and permissions keep identical sources byte
                    # identical across machines and packaging times.
                    info = ZipInfo(path.relative_to(stage).as_posix(), (1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    info.compress_type = ZIP_DEFLATED
                    archive.writestr(info, path.read_bytes(), compresslevel=9)
            os.replace(archive_path, output)
        finally:
            if archive_path is not None:
                archive_path.unlink(missing_ok=True)
    print(f'Created {output} for {args.origin}')


if __name__ == '__main__':
    main()
