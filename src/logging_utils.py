from datetime import datetime
import os
import sys
from typing import Literal

LogLevel = Literal['DEBUG','INFO','WARN','ERROR']
_LEVEL_ORDER = {'DEBUG':10,'INFO':20,'WARN':30,'ERROR':40}
DEFAULT_LEVEL = os.getenv('FORMS_AI_LOG_LEVEL','INFO').upper()

COLOR = os.getenv('FORMS_AI_LOG_COLOR','1') != '0'
_COLORS = {
    'DEBUG':'\x1b[36m',  # cyan
    'INFO':'\x1b[32m',   # green
    'WARN':'\x1b[33m',   # yellow
    'ERROR':'\x1b[31m',  # red
    'RESET':'\x1b[0m'
}

def _allow(level: str) -> bool:
    return _LEVEL_ORDER.get(level, 100) >= _LEVEL_ORDER.get(DEFAULT_LEVEL,20)

def log(component: str, message: str, level: LogLevel = 'INFO', indent: int = 0, end: str='\n') -> None:
    """Unified lightweight logger.
    component: logical module (PIPELINE, SCRAPE, OCR, LLM, CLEANUP, VALIDATE...)
    indent: number of two-space indents before message body (not before header)
    """
    level = level.upper()
    if not _allow(level):
        return
    ts = datetime.now().strftime('%H:%M:%S')
    prefix = f"[{ts}][{level}][{component}]"
    body_indent = '  ' * max(indent,0)
    if COLOR and sys.stdout.isatty():
        color = _COLORS.get(level,'')
        reset = _COLORS['RESET']
        sys.stdout.write(f"{color}{prefix}{reset} {body_indent}{message}{end}")
    else:
        sys.stdout.write(f"{prefix} {body_indent}{message}{end}")
    sys.stdout.flush()

def log_section(title: str, char: str='='):
    line = char* max(len(title), 40)
    log('PIPELINE', line)
    log('PIPELINE', title)
    log('PIPELINE', line)
