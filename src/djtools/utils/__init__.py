"""The "utils" package contains modules for a variety of different tasks.
    * local_dirs_checker.py: Check local tracks for overlap with those already
        in the beatcloud.
    * youtube_dl.py: Download tracks from a URL (e.g. Soundcloud playlist).
"""
from .config import build_config
from .helpers import upload_log
from .local_dirs_checker import check_local_dirs
from .youtube_dl import youtube_dl


UTILS_OPERATIONS = {
    "CHECK_TRACK_OVERLAP": check_local_dirs,
    "YOUTUBE_DL": youtube_dl,
}

__all__ = (
    "build_config",
    "check_local_dirs",
    "upload_log",
    "youtube_dl",
)
