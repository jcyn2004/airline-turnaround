"""
Patches langchain_google_genai/chat_models.py to print the 'tools' payload
right before the failing generate_content call, so we can see the exact
schema being sent to Gemini.

v3 fix: the previous version printed `request.get("tools")`, which came
back as `null`. That's because in this SDK version, generate_content is
called as generate_content(model=..., contents=..., config=...) -- tools
live nested inside `config` (a GenerateContentConfig object), not as a
top-level key on `request`. This version digs into `request["config"]`
and handles both dict-style and Pydantic-object-style configs.

Verified with ast.parse() against the user's actual file before being
handed back, and auto-reverts if the patched file fails to parse.

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

# (relative_indent_spaces, line) -- relative_indent is on top of the base
# indentation of the `try:` line we insert before.
DEBUG_BLOCK = [
    (0, "import json as _json"),
    (0, '_config = request.get("config")'),
    (0, '_tools = _config.get("tools") if isinstance(_config, dict) else getattr(_config, "tools", None)'),
    (0, "def _ser(o):"),
    (4, 'if hasattr(o, "model_dump"):'),
    (8, "return o.model_dump()"),
    (4, 'if hasattr(o, "__dict__"):'),
    (8, "return o.__dict__"),
    (4, "return str(o)"),
    (0, f'print("{MARKER} REQUEST KEYS:", list(request.keys()))'),
    (0, f'print("{MARKER} CONFIG TYPE:", type(_config).__name__)'),
    (0, f'print("{MARKER}", _json.dumps(_tools, indent=2, default=_ser))'),
]


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
    base_indent = try_line[: len(try_line) - len(try_line.lstrip())]

    new_lines = [
        f"{base_indent}{' ' * rel}{text}\n" for rel, text in DEBUG_BLOCK
    ]

    if not BACKUP.exists():
        shutil.copy(TARGET, BACKUP)
        print(f"Backup saved to {BACKUP}")

    lines[target_idx:target_idx] = new_lines
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
