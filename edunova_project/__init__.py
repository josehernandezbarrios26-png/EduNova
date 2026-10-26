import sys
from pathlib import Path

_INNER_DIR = Path(__file__).resolve().parent.parent / 'EduNova-master'
if str(_INNER_DIR) not in sys.path:
    sys.path.insert(0, str(_INNER_DIR))

_INNER_PACKAGE = _INNER_DIR / 'edunova_project'
if _INNER_PACKAGE.exists() and str(_INNER_PACKAGE) not in __path__:
    __path__.append(str(_INNER_PACKAGE))
