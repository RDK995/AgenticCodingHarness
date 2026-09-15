#!/usr/bin/env python3
"""Start Claude Code with foreground subagent execution required by implement-v3."""

from __future__ import annotations

import os
import sys


def main() -> None:
    environment = dict(os.environ)
    environment["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] = "1"
    os.execvpe("claude", ["claude", *sys.argv[1:]], environment)


if __name__ == "__main__":
    main()
