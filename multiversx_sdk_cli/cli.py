import argparse
import logging
import sys
from argparse import ArgumentParser
from typing import Any, List

from rich.logging import RichHandler

import multiversx_sdk_cli.cli_accounts
import multiversx_sdk_cli.cli_config
import multiversx_sdk_cli.cli_contracts
import multiversx_sdk_cli.cli_data
import multiversx_sdk_cli.cli_delegation
import multiversx_sdk_cli.cli_deps
import multiversx_sdk_cli.cli_dns
import multiversx_sdk_cli.cli_ledger
import multiversx_sdk_cli.cli_localnet
import multiversx_sdk_cli.cli_transactions
import multiversx_sdk_cli.cli_validators
import multiversx_sdk_cli.cli_wallet
import multiversx_sdk_cli.version
from multiversx_sdk_cli import config, errors, ux

logger = logging.getLogger("cli")


def main(cli_args: List[str] = sys.argv[1:]):
    try:
        _do_main(cli_args)
    except errors.KnownError as err:
        logger.critical(err.get_pretty())
        ux.show_critical_error(err.get_pretty())
        return 1
    except KeyboardInterrupt:
        print("process killed by user.")
        return 1
    return 0


def _do_main(cli_args: List[str]):
    argv_with_config_args = config.add_config_args(cli_args)
    parser = setup_parser(argv_with_config_args)
    args = parser.parse_args(argv_with_config_args)

    if args.verbose:
        logging.basicConfig(level="DEBUG", force=True, format='%(name)s: %(message)s', handlers=[RichHandler(show_time=False, rich_tracebacks=True)])
    else:
        logging.basicConfig(level="INFO", format='%(name)s: %(message)s', handlers=[RichHandler(show_time=False, rich_tracebacks=True)])

    if not hasattr(args, "func"):
        parser.print_help()
    else:
        args.func(args)


def setup_parser(args: List[str]):
    parser = ArgumentParser(
        prog="mxpy",
        usage="mxpy [-h] [-v] [--verbose] COMMAND-GROUP [-h] COMMAND ...",
        description="""
-----------
DESCRIPTION
-----------
mxpy is part of the multiversx-sdk and consists of Command Line Tools and Python SDK
for interacting with the Blockchain (in general) and with Smart Contracts (in particular).

mxpy targets a broad audience of users and developers.
https://docs.multiversx.com/sdk-and-tools/mxpy.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser._positionals.title = "COMMAND GROUPS"
    parser._optionals.title = "TOP-LEVEL OPTIONS"
    version = multiversx_sdk_cli.version.get_version()
    parser.add_argument("-v", "--version", action="version", version=f"MultiversX Python CLI (mxpy) {version}")
    parser.add_argument("--verbose", action="store_true", default=False)

    subparsers = parser.add_subparsers()
    commands: List[Any] = []

    commands.append(multiversx_sdk_cli.cli_contracts.setup_parser(args, subparsers))
    commands.append(multiversx_sdk_cli.cli_transactions.setup_parser(args, subparsers))
    commands.append(multiversx_sdk_cli.cli_validators.setup_parser(args, subparsers))
    commands.append(multiversx_sdk_cli.cli_accounts.setup_parser(subparsers))
    commands.append(multiversx_sdk_cli.cli_ledger.setup_parser(subparsers))
    commands.append(multiversx_sdk_cli.cli_wallet.setup_parser(args, subparsers))
    commands.append(multiversx_sdk_cli.cli_deps.setup_parser(subparsers))
    commands.append(multiversx_sdk_cli.cli_config.setup_parser(subparsers))
    commands.append(multiversx_sdk_cli.cli_localnet.setup_parser(args, subparsers))
    commands.append(multiversx_sdk_cli.cli_data.setup_parser(subparsers))
    commands.append(multiversx_sdk_cli.cli_delegation.setup_parser(args, subparsers))
    commands.append(multiversx_sdk_cli.cli_dns.setup_parser(args, subparsers))

    parser.epilog = """
----------------------
COMMAND GROUPS summary
----------------------
"""
    for choice, sub in subparsers.choices.items():
        parser.epilog += (f"{choice.ljust(30)} {sub.description}\n")

    return parser


if __name__ == "__main__":
    ret = main(sys.argv[1:])
    sys.exit(ret)
