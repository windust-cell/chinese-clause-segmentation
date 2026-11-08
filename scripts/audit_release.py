"""Check tracked release scope and common sensitive strings before committing.

This check supplements manual review; it is not a complete secret detector.
Run after git add from the repository root. Build archives are checked too.
"""
import re
import subprocess
import tarfile
import zipfile
from pathlib import Path

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
    # The scanner's own patterns are not credentials or actual local paths.
    if name.endswith("scripts/audit_release.py") or name == "scripts/audit_release.py":
        return
    if any(pattern.search(text) for pattern in PATTERNS):
        raise SystemExit(f"Sensitive string candidate: {name}")


def main():
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
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
    archives = list((ROOT/"dist").glob("*.whl")) + list((ROOT/"dist").glob("*.tar.gz"))
    for archive in archives:
        if archive.suffix == ".whl":
            with zipfile.ZipFile(archive) as bundle:
                for name in bundle.namelist():
                    if name.endswith((".pyc", ".csv", ".xlsx")):
                        raise SystemExit(f"Unexpected bundled data: {name}")
                    inspect(name, bundle.read(name))
        else:
            with tarfile.open(archive) as bundle:
                for member in bundle.getmembers():
                    if member.isfile():
                        inspect(member.name, bundle.extractfile(member).read())
    print(f"PASS: {len(files)} tracked files and {len(archives)} archives; manual review still required")


if __name__ == "__main__":
    main()
