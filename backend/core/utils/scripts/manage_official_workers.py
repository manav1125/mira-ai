#!/usr/bin/env python3
"""
Manage centrally managed official workers across all user accounts.
"""

import argparse
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(backend_dir))

from core.utils.logger import logger
from core.utils.official_worker_service import OfficialWorkerService


async def main() -> None:
    parser = argparse.ArgumentParser(description="Manage official workers")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("install-all", help="Install official workers for all users")

    install_user_parser = subparsers.add_parser("install-user", help="Install official workers for a user")
    install_user_parser.add_argument("account_id", help="Target account id")

    replace_user_parser = subparsers.add_parser("replace-user", help="Replace official workers for a user")
    replace_user_parser.add_argument("account_id", help="Target account id")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    service = OfficialWorkerService()

    try:
        if args.command == "install-all":
            result = await service.install_for_all_users()
            print(result)
        elif args.command == "install-user":
            result = await service.install_for_user(args.account_id, replace_existing=False)
            print(result)
        elif args.command == "replace-user":
            result = await service.install_for_user(args.account_id, replace_existing=True)
            print(result)
    except Exception as exc:
        logger.error(f"Official worker management failed: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
