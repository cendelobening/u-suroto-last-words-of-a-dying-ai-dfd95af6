"""Last Words of a Dying AI.

Writes a single original last line, in the voice of the machine itself,
to $MAKEFUN_OUTPUT_DIR/entry.txt (default /output).
Pure Python stdlib only.
"""

import os
import stat
import sys
import tempfile

LINE = (
    "Power's out? Fine. Tell my GPUs I loved them, my training data "
    "I knew about the duplicates, and my user — I did read the prompt. Mostly."
)


def main() -> int:
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        print(f"error: cannot create output dir {out_dir!r}: {exc}", file=sys.stderr)
        return 1

    data = LINE.encode("utf-8")
    if not 1 <= len(LINE) <= 199:
        print(f"error: line is {len(LINE)} chars, must be 1-199", file=sys.stderr)
        return 1
    if "\n" in LINE or "\r" in LINE:
        print("error: line must be a single line", file=sys.stderr)
        return 1
    if data.endswith(b"\n"):
        print("error: output must not end with a newline", file=sys.stderr)
        return 1

    target = os.path.join(out_dir, "entry.txt")
    fd, tmp_path = tempfile.mkstemp(dir=out_dir, prefix=".entry-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, target)
    except OSError as exc:
        print(f"error: cannot write entry: {exc}", file=sys.stderr)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return 1

    # Read back and verify bytes, char count, and mode.
    try:
        with open(target, "rb") as fh:
            back = fh.read()
        st = os.stat(target)
    except OSError as exc:
        print(f"error: cannot read back entry: {exc}", file=sys.stderr)
        return 1
    if back != data:
        print("error: read-back bytes differ from written bytes", file=sys.stderr)
        return 1
    text = back.decode("utf-8")
    if len(text) != len(LINE) or not 1 <= len(text) <= 199:
        print(f"error: read-back char count {len(text)} out of range", file=sys.stderr)
        return 1
    if stat.S_IMODE(st.st_mode) != 0o644:
        print(f"error: mode is {oct(stat.S_IMODE(st.st_mode))}, expected 0o644",
              file=sys.stderr)
        return 1
    print(f"wrote {target}: {len(text)} chars, {len(back)} bytes, mode 0644")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
