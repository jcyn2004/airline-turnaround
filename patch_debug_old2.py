"""
Patches langchain_google_genai/chat_models.py to print the 'tools' payload
right before the failing generate_content call, so we can see the exact
schema being sent to Gemini.

Fixes vs. earlier versions:
1. The generate_content(...) call is the middle of a multi-line expression
   (response = (await ...)), not a standalone statement. Inserting there
   breaks syntax. This inserts before the preceding `try:` line instead,
   which is a safe boundary between two full statements.
2. The file has BOTH a sync `_generate` and an async `_agenerate` method,
   each with their own try/generate_content block. An unscoped search finds
   the wrong (sync) one. This version scopes the search to start only after
   `async def _agenerate`, matching the method that actually appears in your
   traceback.

Verified against the user's actual chat_models.py with ast.parse() before
being handed back.

Usage:
    python patch_debug.py            # apply the patch
    python patch_debug.py --undo     # restore the original file from backup
"""
import sys
import shutil
from pathlib import Path

TARGET = Path(
    "/Users/jc/Projects/airline-turnaround/venv/lib/python3.14/"
    "site-packages/langchain_google_genai/chat_models.py"
)
BACKUP = TARGET.with_suffix(TARGET.suffix + ".bak")

MARKER = "=== GEMINI TOOLS PAYLOAD ==="
METHOD_MARKER = "async def _agenerate"
CALL_SNIPPET = "generate_content("
LOOKAHEAD = 6  # how many lines after `try:` to look for the call


def undo():
    if not BACKUP.exists():
        print(f"No backup found at {BACKUP}. Nothing to undo.")
        return
    shutil.copy(BACKUP, TARGET)
    print(f"Restored original file from {BACKUP}")


def find_insertion_point(lines):
    """Find the `try:` line inside async def _agenerate that precedes
    a generate_content( call."""
    start = None
    for i, line in enumerate(lines):
        if METHOD_MARKER in line:
            start = i
            break
    if start is None:
        return None

    for i in range(start, len(lines)):
        if lines[i].strip() == "try:":
            window = lines[i + 1 : i + 1 + LOOKAHEAD]
            if any(CALL_SNIPPET in w for w in window):
                return i
    return None


def apply_patch():
    if not TARGET.exists():
        print(f"Could not find file at {TARGET}")
        print("Update the TARGET path at the top of this script if your venv path differs.")
        sys.exit(1)

    lines = TARGET.read_text().splitlines(keepends=True)

    if any(MARKER in line for line in lines):
        print("Debug print already present. Skipping (run with --undo first if you want to re-patch).")
        return

    target_idx = find_insertion_point(lines)
    if target_idx is None:
        print(f"Could not find the `try:` block inside `{METHOD_MARKER}`.")
        print("The file may differ from what we expect; you'll need to locate it manually.")
        sys.exit(1)

    try_line = lines[target_idx]
    indent = try_line[: len(try_line) - len(try_line.lstrip())]

    debug_line = (
        f'{indent}import json as _json; '
        f'print("{MARKER}", _json.dumps(request.get("tools"), indent=2, default=str))\n'
    )

    if not BACKUP.exists():
        shutil.copy(TARGET, BACKUP)
        print(f"Backup saved to {BACKUP}")

    lines.insert(target_idx, debug_line)
    TARGET.write_text("".join(lines))

    # Sanity check before declaring success
    import ast
    try:
        ast.parse(TARGET.read_text())
    except SyntaxError as e:
        print(f"WARNING: patched file failed to parse ({e}). Restoring backup.")
        shutil.copy(BACKUP, TARGET)
        sys.exit(1)

    print(f"Patched {TARGET} before line {target_idx + 1} ('try:' inside {METHOD_MARKER})")
    print("Syntax verified OK.")
    print("Now rerun whatever command originally triggered the error.")


if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo()
    else:
        apply_patch()
