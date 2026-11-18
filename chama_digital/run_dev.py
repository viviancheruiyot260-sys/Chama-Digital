#!/usr/bin/env python3
"""Safe development/start server launcher for Chama Digital.

Handles optional CLI flags (such as --port or --host) forwarded by package
managers or process supervisors without failing Django's runserver parser.
"""
import argparse
import os
import sys
from pathlib import Path


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    os.environ.setdefault('PYTHONUNBUFFERED', '1')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chama_digital.settings')

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--port', default=os.environ.get('PORT', '3000'))
    parser.add_argument('--host', default=os.environ.get('HOST', '0.0.0.0'))
    args, _unknown = parser.parse_known_args(sys.argv[1:])

    import django
    from django.core.management import execute_from_command_line

    django.setup()
    from chama_digital.db_bootstrap import ensure_database_ready
    ensure_database_ready()

    execute_from_command_line([
        str(base_dir / 'manage.py'),
        'runserver',
        f'{args.host}:{args.port}',
        '--noreload',
    ])


if __name__ == '__main__':
    main()
