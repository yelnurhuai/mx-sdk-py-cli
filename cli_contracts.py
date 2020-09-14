import logging
import os
from typing import Any

from erdpy import cli_shared, errors, projects, utils
from erdpy.accounts import Account, Address
from erdpy.contracts import CodeMetadata, SmartContract
from erdpy.projects import load_project
from erdpy.proxy.core import ElrondProxy

logger = logging.getLogger("cli.contracts")


def setup_parser(subparsers: Any) -> Any:
    parser = cli_shared.add_group_subparser(subparsers, "contract", "Build, deploy and interact with Smart Contracts")
    subparsers = parser.add_subparsers()

    sub = cli_shared.add_command_subparser(subparsers, "contract", "new", "Create a new Smart Contract project based on a template.")
    sub.add_argument("name")
    sub.add_argument("--template", required=True, help="the template to use")
    sub.add_argument("--directory", type=str, default=os.getcwd(), help="🗀 the parent directory of the project (default: current directory)")
    sub.set_defaults(func=create)

    sub = cli_shared.add_command_subparser(subparsers, "contract", "templates", "List the available Smart Contract templates.")
    sub.set_defaults(func=list_templates)

    sub = cli_shared.add_command_subparser(subparsers, "contract", "build", "Build a Smart Contract project using the appropriate buildchain.")
    _add_project_arg(sub)
    sub.add_argument("--debug", action="store_true", default=False, help="set debug flag (default: %(default)s)")
    sub.add_argument("--no-optimization", action="store_true", default=False, help="bypass optimizations (for clang) (default: %(default)s)")
    sub.set_defaults(func=build)

    sub = cli_shared.add_command_subparser(subparsers, "contract", "clean", "Clean a Smart Contract project.")
    _add_project_arg(sub)
    sub.set_defaults(func=clean)

    sub = cli_shared.add_command_subparser(subparsers, "contract", "test", "Run Mandos tests.")
    _add_project_arg(sub)
    sub.add_argument("--directory", default="mandos", help="🗀 the directory containing the tests (default: %(default)s)")
    sub.add_argument("--wildcard", required=False, help="wildcard to match only specific test files")
    sub.set_defaults(func=run_tests)

    sub = cli_shared.add_command_subparser(subparsers, "contract", "deploy", "Deploy a Smart Contract.")
    _add_project_or_bytecode_arg(sub)
    _add_metadata_arg(sub)
    cli_shared.add_outfile_arg(sub)
    cli_shared.add_wallet_args(sub)
    cli_shared.add_proxy_arg(sub)
    cli_shared.add_tx_args(sub, with_receiver=False, with_data=False)
    _add_arguments_arg(sub)
    _add_send_arg(sub)

    sub.set_defaults(func=deploy)

    sub = cli_shared.add_command_subparser(subparsers, "contract", "call", "Interact with a Smart Contract (execute function).")
    _add_contract_arg(sub)
    cli_shared.add_outfile_arg(sub)
    cli_shared.add_wallet_args(sub)
    cli_shared.add_proxy_arg(sub)
    cli_shared.add_tx_args(sub, with_receiver=False, with_data=False)
    _add_function_arg(sub)
    _add_arguments_arg(sub)
    _add_send_arg(sub)

    sub.set_defaults(func=call)

    sub = cli_shared.add_command_subparser(subparsers, "contract", "upgrade", "Upgrade a previously-deployed Smart Contract")
    _add_contract_arg(sub)
    cli_shared.add_outfile_arg(sub)
    _add_project_or_bytecode_arg(sub)
    _add_metadata_arg(sub)
    cli_shared.add_wallet_args(sub)
    cli_shared.add_proxy_arg(sub)
    cli_shared.add_tx_args(sub, with_receiver=False, with_data=False)
    _add_arguments_arg(sub)
    _add_send_arg(sub)

    sub.set_defaults(func=upgrade)

    sub = cli_shared.add_command_subparser(subparsers, "contract", "query", "Query a Smart Contract (call a pure function)")
    _add_contract_arg(sub)
    cli_shared.add_proxy_arg(sub)
    _add_function_arg(sub)
    _add_arguments_arg(sub)
    sub.set_defaults(func=query)

    parser.epilog = cli_shared.build_group_epilog(subparsers)
    return subparsers


def _add_project_arg(sub: Any):
    sub.add_argument("project", nargs='?', default=os.getcwd(), help="🗀 the project directory (default: current directory)")


def _add_project_or_bytecode_arg(sub: Any):
    group = sub.add_mutually_exclusive_group(required=True)
    group.add_argument("--project", default=os.getcwd(), help="🗀 the project directory (default: current directory)")
    group.add_argument("--bytecode", help="the WASM file")


def _add_contract_arg(sub: Any):
    sub.add_argument("contract", help="🖄 the address of the Smart Contract")


def _add_function_arg(sub: Any):
    sub.add_argument("--function", required=True, help="the function to call")


def _add_arguments_arg(sub: Any):
    sub.add_argument("--arguments", nargs='+', help="arguments for the contract transaction, as numbers or hex-encoded. E.g. --arguments 42 0x64 1000 0xabba")


def _add_metadata_arg(sub: Any):
    sub.add_argument("--metadata-not-upgradeable", dest="metadata_upgradeable", action="store_false", help="‼ mark the contract as NOT upgradeable (default: upgradeable)")
    sub.add_argument("--metadata-payable", dest="metadata_payable", action="store_true", help="‼ mark the contract as payable (default: not payable)")
    sub.set_defaults(metadata_upgradeable=True, metadata_payable=False)


def _add_send_arg(sub: Any):
    sub.add_argument("--send", action="store_true", default=False, help="✓ whether to broadcast the transaction (default: %(default)s)")


def list_templates(args: Any):
    projects.list_project_templates()


def create(args: Any):
    name = args.name
    template = args.template
    directory = args.directory

    projects.create_from_template(name, template, directory)


def clean(args: Any):
    project = args.project
    projects.clean_project(project)


def build(args: Any):
    project = args.project
    options = {
        "debug": args.debug,
        "optimized": not args.no_optimization,
        "verbose": args.verbose
    }

    projects.build_project(project, options)


def run_tests(args: Any):
    projects.run_tests(args)


def deploy(args: Any):
    logger.debug("deploy")

    arguments = args.arguments
    gas_price = args.gas_price
    gas_limit = args.gas_limit
    value = args.value
    chain = args.chain
    version = args.version

    contract = _prepare_contract(args)
    sender = _prepare_sender(args)

    tx = contract.deploy(sender, arguments, gas_price, gas_limit, value, chain, version)
    logger.info("Contract address: %s", contract.address)

    try:
        if args.send:
            tx.send(ElrondProxy(args.proxy))
    finally:
        tx.dump_to(args.outfile, extra={"address": contract.address.bech32()})


def _prepare_contract(args: Any) -> SmartContract:
    if args.bytecode:
        bytecode = utils.read_file(args.bytecode, binary=True).hex()
    else:
        project = load_project(args.project)
        bytecode = project.get_bytecode()

    metadata = CodeMetadata(args.metadata_upgradeable, args.metadata_payable)
    contract = SmartContract(bytecode=bytecode, metadata=metadata)
    return contract


def _prepare_sender(args: Any) -> Account:
    if args.pem:
        sender = Account(pem_file=args.pem, pem_index=args.pem_index)
    elif args.keyfile and args.passfile:
        sender = Account(key_file=args.keyfile, pass_file=args.passfile)
    else:
        raise errors.NoWalletProvided()

    sender.nonce = args.nonce
    if args.recall_nonce:
        sender.sync_nonce(ElrondProxy(args.proxy))

    return sender


def call(args: Any):
    logger.debug("call")

    contract_address = args.contract
    function = args.function
    arguments = args.arguments
    gas_price = args.gas_price
    gas_limit = args.gas_limit
    value = args.value
    chain = args.chain
    version = args.version

    contract = SmartContract(contract_address)
    sender = _prepare_sender(args)

    tx = contract.execute(sender, function, arguments, gas_price, gas_limit, value, chain, version)
    try:
        if args.send:
            tx.send(ElrondProxy(args.proxy))
    finally:
        tx.dump_to(args.outfile)


def upgrade(args: Any):
    logger.debug("upgrade")

    contract_address = args.contract
    arguments = args.arguments
    gas_price = args.gas_price
    gas_limit = args.gas_limit
    value = args.value
    chain = args.chain
    version = args.version

    contract = _prepare_contract(args)
    contract.address = Address(contract_address)
    sender = _prepare_sender(args)

    tx = contract.upgrade(sender, arguments, gas_price, gas_limit, value, chain, version)
    try:
        if args.send:
            tx.send(ElrondProxy(args.proxy))
    finally:
        tx.dump_to(args.outfile)


def query(args: Any):
    logger.debug("query")

    contract_address = args.contract
    function = args.function
    arguments = args.arguments

    contract = SmartContract(contract_address)
    result = contract.query(ElrondProxy(args.proxy), function, arguments)
    print(result)
