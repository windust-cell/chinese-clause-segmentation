"""Check tracked release scope and common sensitive strings before committing.

This check supplements manual review; it is not a complete secret detector.
Run from the repository root, or use --archives-only --archive PATH.
"""
import re
import argparse
import stat
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"src", "tests", "benchmarks", "examples", "docs", "evaluation", "scripts", ".github"}
ROOT_FILES = {"README.md", "LICENSE", "pyproject.toml", ".gitignore", "MANIFEST.in"}
PATTERNS = [
    re.compile(r"[A-Za-z]:[\\/]|/Users/|/home/"),
    re.compile(r"(?<![\w])\d{10}(?![\w])"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def inspect(name, payload):
    text = payload.decode("utf-8", errors="replace")
    for line in text.splitlines():
        # Exempt only this exact detector definition, never the whole file.
        if name.endswith('scripts/audit_release.py') and line.strip() == f're.compile(r"{PATTERNS[0].pattern}"),':
            continue
        if any(pattern.search(line) for pattern in PATTERNS):
            raise SystemExit(f"Sensitive string candidate: {name}")


def check_member(name, *, link=False, special=False):
    normalized = name.replace('\\', '/')
    parts = PurePosixPath(normalized).parts
    if not parts or normalized.startswith('/') or '..' in parts or any(':' in part for part in parts):
        raise SystemExit(f"Unsafe archive path: {name}")
    if link or special:
        raise SystemExit(f"Links and special archive entries are not permitted: {name}")
    if PurePosixPath(normalized).suffix.lower() in {'.pyc', '.csv', '.xlsx', '.parquet', '.pkl', '.npy', '.jsonl', '.log', '.db', '.sqlite'} or PurePosixPath(normalized).name == '.env':
        raise SystemExit(f"Unexpected bundled file: {name}")


def audit_archive(path):
    total = 0
    seen = set()
    def member(name, size, **options):
        nonlocal total
        check_member(name, **options)
        normalized = name.replace('\\', '/').rstrip('/').casefold()
        if normalized in seen:
            raise SystemExit(f'Duplicate archive path: {name}')
        seen.add(normalized)
        total += size
        if size > 16*1024*1024 or total > 128*1024*1024 or len(seen) > 10000:
            raise SystemExit('Archive exceeds release audit resource limits')
    if path.suffix in ('.whl', '.zip'):
        with zipfile.ZipFile(path) as bundle:
            for entry in bundle.infolist():
                kind = stat.S_IFMT(entry.external_attr >> 16)
                member(entry.filename, entry.file_size, link=kind == stat.S_IFLNK,
                       special=kind not in (0, stat.S_IFREG, stat.S_IFDIR, stat.S_IFLNK))
                inspect(entry.filename, bundle.read(entry))
    else:
        with tarfile.open(path) as bundle:
            for entry in bundle:
                member(entry.name, entry.size, link=entry.issym() or entry.islnk(),
                       special=not (entry.isfile() or entry.isdir() or entry.issym() or entry.islnk()))
                if entry.isfile():
                    inspect(entry.name, bundle.extractfile(entry).read())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, action='append', default=[])
    parser.add_argument('--archives-only', action='store_true')
    args = parser.parse_args()
    if args.archives_only:
        if not args.archive:
            parser.error('--archives-only requires --archive')
        for archive in args.archive:
            audit_archive(archive)
        print(f'PASS: {len(args.archive)} archives; no files modified')
        return
    files = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    files = [name for name in files if name]
    if not files:
        raise SystemExit("No staged/tracked files")
    for name in files:
        path = Path(name)
        if path.parts[0] not in ALLOWED and name not in ROOT_FILES:
            raise SystemExit(f"Unexpected release file: {name}")
        if path.suffix in {".csv", ".xlsx", ".parquet", ".npy", ".pkl"}:
            raise SystemExit(f"Data file excluded: {name}")
        inspect(name, (ROOT/name).read_bytes())
    archives = args.archive or (list((ROOT/"dist").glob("*.whl")) + list((ROOT/"dist").glob("*.tar.gz")))
    for archive in archives:
        audit_archive(archive)
    print(f"PASS: {len(files)} tracked/untracked files and {len(archives)} archives; manual review still required")


if __name__ == "__main__":
    main()
