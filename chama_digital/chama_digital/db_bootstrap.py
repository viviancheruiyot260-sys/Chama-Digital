"""Automatic SQLite bootstrap & self-healing migration helper for Chama Digital.

If db.sqlite3 is missing or reset (e.g. fresh checkout or deleted database file),
this module runs migrations and seeds initial demo chama data automatically so
views, sessions, and authentication never fail with 'no such table' errors.
"""
import sys
import threading
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import connection, connections

_DB_LOCK = threading.Lock()
_VERIFIED_INODE = None


def ensure_database_ready() -> None:
    global _VERIFIED_INODE

    # Never interfere with Django's test runner
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        return

    db_conf = settings.DATABASES.get('default', {})
    if db_conf.get('ENGINE') != 'django.db.backends.sqlite3':
        return

    db_name = str(db_conf.get('NAME', ''))
    if not db_name or db_name == ':memory:' or db_name.startswith('file:memorydb'):
        return

    db_path = Path(db_name)
    try:
        st = db_path.stat()
        if st.st_size >= 4096 and _VERIFIED_INODE == (st.st_dev, st.st_ino):
            return
    except FileNotFoundError:
        pass

    with _DB_LOCK:
        try:
            st = db_path.stat()
            if st.st_size >= 4096 and _VERIFIED_INODE == (st.st_dev, st.st_ino):
                return
        except FileNotFoundError:
            pass

        db_path.parent.mkdir(parents=True, exist_ok=True)
        connections.close_all()

        tables = set(connection.introspection.table_names())
        if 'accounts_chamagroup' not in tables:
            call_command('migrate', '--noinput', verbosity=0)

        from accounts.models import ChamaGroup
        if not ChamaGroup.objects.exists():
            call_command('seed_chama_data')

        try:
            st = db_path.stat()
            _VERIFIED_INODE = (st.st_dev, st.st_ino)
        except FileNotFoundError:
            _VERIFIED_INODE = None
