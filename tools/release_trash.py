"""Delete release trash (beops-trash-<32 hex>) in the background, without touching shared files.

A release workspace links sealed closed months and evidence (same inode as the live record). The
read-only attribute on those inodes IS the seal. Deleting a read-only link name the usual way
(attrib -r, del /f) clears that attribute on the live file too - and a release in flight that has
just linked the same month then fails its own identity check. Here a read-only name is removed
with POSIX delete semantics and FILE_DISPOSITION_IGNORE_READONLY_ATTRIBUTE (Windows 10 1809+,
NTFS): the name disappears, the attributes of the shared file do not change. Junctions are
removed, never followed. Runs at idle priority, holds no publication lock.

    python tools/release_trash.py <releases-dir> [beops-trash-<hex> ...]   # delete owned trash folders
"""
import ctypes
import os
import pathlib
import re
import stat
import sys

TRASH = re.compile(r'^beops-trash-[a-f0-9]{32}$')
MARKER = '.beops-generated-workspace.json'
SENTINEL = '.beops-trash-deleting'  # survives an interrupted deletion, removed last


def _ignore_readonly_delete(path):
    from ctypes import wintypes
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    k32.SetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    DELETE, SHARE_ALL, OPEN_EXISTING = 0x00010000, 0x7, 3
    FLAGS = 0x00200000 | 0x02000000  # OPEN_REPARSE_POINT | BACKUP_SEMANTICS
    handle = k32.CreateFileW(str(path), DELETE, SHARE_ALL, None, OPEN_EXISTING, FLAGS, None)
    if handle in (None, wintypes.HANDLE(-1).value):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        info = wintypes.DWORD(0x1 | 0x2 | 0x10)  # DELETE | POSIX_SEMANTICS | IGNORE_READONLY_ATTRIBUTE
        if not k32.SetFileInformationByHandle(handle, 21, ctypes.byref(info), ctypes.sizeof(info)):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        k32.CloseHandle(handle)


def remove_name(path):
    try:
        os.remove(path)
    except PermissionError:
        if os.name != 'nt':
            raise
        _ignore_readonly_delete(path)


def is_link_dir(entry):
    try:
        if entry.is_symlink() or getattr(entry, 'is_junction', lambda: False)():
            return True
        return bool(entry.stat(follow_symlinks=False).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT) \
            if os.name == 'nt' else False
    except OSError:
        return True


def delete_tree(root):
    root = pathlib.Path(root)
    removed = 0
    stack = [(root, False)]
    while stack:
        folder, visited = stack.pop()
        if visited:
            if folder == root and (root / SENTINEL).exists():
                remove_name(root / SENTINEL)
            os.rmdir(folder)
            continue
        stack.append((folder, True))
        with os.scandir(folder) as entries:
            for entry in entries:
                if folder == root and entry.name == SENTINEL:
                    continue
                if entry.is_dir(follow_symlinks=False) and not is_link_dir(entry):
                    stack.append((pathlib.Path(entry.path), False))
                elif entry.is_dir(follow_symlinks=False) or is_link_dir(entry):
                    os.rmdir(entry.path) if entry.is_dir(follow_symlinks=False) else remove_name(entry.path)
                else:
                    remove_name(entry.path)
                    removed += 1
    return removed


def owned_trash(base):
    base = pathlib.Path(base)
    for item in sorted(base.iterdir()) if base.is_dir() else []:
        if (TRASH.match(item.name) and item.is_dir() and not item.is_symlink()
                and ((item / MARKER).is_file() or (item / SENTINEL).is_file())):
            yield item


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[-1].strip())
        return 2
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x40)  # IDLE
        except Exception:
            pass
    only = set(argv[2:])  # the publisher names the folders it marked; nothing else is touched by this run
    total = 0
    for item in owned_trash(argv[1]):
        if only and item.name not in only:
            continue
        (item / SENTINEL).touch()
        total += delete_tree(item)
        print('removed release trash: %s (%d files)' % (item.name, total))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
