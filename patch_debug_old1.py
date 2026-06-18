"""
Patches langchain_google_genai/chat_models.py to print the 'tools' payload
right before the failing generate_content call, so we can see the exact
schema being sent to Gemini.

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
CALL_SNIPPET = "await self.client.aio.models.generate_content("


def undo():
    if not BACKUP.exists():
        print(f"No backup found at {BACKUP}. Nothing to undo.")
        return
    shutil.copy(BACKUP, TARGET)
    print(f"Restored original file from {BACKUP}")


def apply_patch():
    if not TARGET.exists():
        print(f"Could not find file at {TARGET}")
        print("Update the TARGET path at the top of this script if your venv path differs.")
        sys.exit(1)

    lines = TARGET.read_text().splitlines(keepends=True)

    # Idempotency check: don't patch twice
    if any(MARKER in line for line in lines):
        print("Debug print already present. Skipping (run with --undo first if you want to re-patch).")
        return

    # Find the target call line
    target_idx = None
    for i, line in enumerate(lines):
        if CALL_SNIPPET in line:
            target_idx = i
            break

    if target_idx is None:
        print(f"Could not find a line containing: {CALL_SNIPPET}")
        print("The file may have changed; you'll need to locate the call manually.")
        sys.exit(1)

    # Match the indentation of the target line
    target_line = lines[target_idx]
    indent = target_line[: len(target_line) - len(target_line.lstrip())]

    debug_line = (
        f'{indent}import json as _json; '
        f'print("{MARKER}", _json.dumps(request.get("tools"), indent=2, default=str))\n'
    )

    # Backup original before modifying
    if not BACKUP.exists():
        shutil.copy(TARGET, BACKUP)
        print(f"Backup saved to {BACKUP}")

    lines.insert(target_idx, debug_line)
    TARGET.write_text("".join(lines))
    print(f"Patched {TARGET} at line {target_idx + 1}")
    print("Now rerun whatever command originally triggered the error.")


if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo()
    else:
        apply_patch()
