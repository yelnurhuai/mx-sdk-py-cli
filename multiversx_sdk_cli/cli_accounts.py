import logging
from typing import Any

from multiversx_sdk_core import Address
from multiversx_sdk_network_providers.proxy_network_provider import \
    ProxyNetworkProvider

from multiversx_sdk_cli import cli_shared, utils

logger = logging.getLogger("cli.accounts")


def setup_parser(subparsers: Any) -> Any:
    parser = cli_shared.add_group_subparser(subparsers, "account", "Get Account data (nonce, balance) from the Network")
    subparsers = parser.add_subparsers()

    sub = cli_shared.add_command_subparser(subparsers, "account", "get", "Query account details (nonce, balance etc.)")
    cli_shared.add_proxy_arg(sub)
    _add_address_arg(sub)
    mutex = sub.add_mutually_exclusive_group()
    mutex.add_argument("--balance", action="store_true", help="whether to only fetch the balance")
    mutex.add_argument("--nonce", action="store_true", help="whether to only fetch the nonce")
    mutex.add_argument("--username", action="store_true", help="whether to only fetch the username")
    cli_shared.add_omit_fields_arg(sub)
    sub.set_defaults(func=get_account)

    parser.epilog = cli_shared.build_group_epilog(subparsers)
    return subparsers


def _add_address_arg(sub: Any):
    sub.add_argument("--address", required=True, help="🖄 the address to query")


def get_account(args: Any):
    proxy_url = args.proxy
    address = args.address
    proxy = ProxyNetworkProvider(proxy_url)
    account = proxy.get_account(Address.from_bech32(address))

    if args.balance:
        print(account.balance)
    elif args.nonce:
        print(account.nonce)
    elif args.username:
        print(account.username)
    else:
        utils.dump_out_json(account.to_dictionary())
