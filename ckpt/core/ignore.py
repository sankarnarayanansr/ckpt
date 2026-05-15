import fnmatch
from pathlib import Path
from typing import List


DEFAULT_IGNORE_PATTERNS = [
    # Vivado generated
    "*.cache/*",
    "*.ip_user_files/*",
    "*.sim/*",
    "*.hbs",
    "*.log",
    "*.jou",
    "*.str",
    "vivado_*.backup.jou",
    "vivado_*.backup.log",
    # Quartus generated
    "db/*",
    "incremental_db/*",
    "*.rpt",
    "*.pin",
    "*.smsg",
    "*.summary",
    "*.done",
    # ModelSim / Questa
    "work/*",
    "transcript",
    "vsim.wlf",
    # General
    "__pycache__/*",
    "*.pyc",
    ".DS_Store",
    "Thumbs.db",
]


class IgnoreRules:
    def __init__(self, patterns: List[str]):
        self.patterns = patterns

    @classmethod
    def load(cls, root: Path) -> "IgnoreRules":
        patterns = list(DEFAULT_IGNORE_PATTERNS)
        ignore_file = root / ".ckptignore"
        if ignore_file.exists():
            for line in ignore_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
        return cls(patterns)

    def match(self, rel_path: str) -> bool:
        """Return True if the file should be ignored."""
        for pattern in self.patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # Also match against just the filename
            filename = Path(rel_path).name
            if fnmatch.fnmatch(filename, pattern.rstrip("/*")):
                return True
        return False
