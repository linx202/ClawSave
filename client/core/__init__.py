# ClawSave Client Core Module

from .config_manager import ConfigManager
from .file_handler import (
    expand_path,
    pack_directory,
    unpack_archive,
    generate_archive_filename,
    get_directory_size,
)
from .meta_manager import (
    create_meta,
    add_backup,
    update_latest,
    get_note,
    set_note,
    remove_note,
    list_backups,
    get_latest_backup,
    get_backup_count,
    remove_backup,
    to_json,
    from_json,
    validate_meta,
)
from .webdav_client import WebDAVClient, WebDAVError
from .retry_handler import with_retry, RetryExhausted
from .library_manager import LibraryManager, get_library_manager

__all__ = [
    # Config
    'ConfigManager',
    # File Handler
    'expand_path',
    'pack_directory',
    'unpack_archive',
    'generate_archive_filename',
    'get_directory_size',
    # Meta Manager
    'create_meta',
    'add_backup',
    'update_latest',
    'get_note',
    'set_note',
    'remove_note',
    'list_backups',
    'get_latest_backup',
    'get_backup_count',
    'remove_backup',
    'to_json',
    'from_json',
    'validate_meta',
    # WebDAV
    'WebDAVClient',
    'WebDAVError',
    # Retry
    'with_retry',
    'RetryExhausted',
    # Library
    'LibraryManager',
    'get_library_manager',
]
