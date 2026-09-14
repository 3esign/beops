"""G-593: sibling staging for durable project artifacts, with parent permissions.

Do not use this for secrets or process-private scratch. Python tempfile.mkdtemp
uses mode 0700: on current Windows it installs a protected owner-only ACL. A
later directory rename preserves that ACL and strands the artifact when its
creator account changes. Ordinary mkdir inherits the existing project ACL.
"""
import pathlib
import re
import uuid


def create_artifact_staging(parent, prefix=".artifact-"):
    parent = pathlib.Path(parent).resolve(strict=True)
    if not parent.is_dir():
        raise NotADirectoryError(parent)
    if not re.fullmatch(r"[.A-Za-z0-9_-]{1,60}", prefix) or prefix in (".", ".."):
        raise ValueError("staging prefix must be one filename component")
    for _ in range(64):
        candidate = parent / (prefix + uuid.uuid4().hex)
        try:
            # Windows: inherit DACL. POSIX: ordinary directory mode + process umask.
            candidate.mkdir(mode=0o777)
            return candidate
        except FileExistsError:
            continue
    raise FileExistsError("could not reserve unique artifact staging directory")
