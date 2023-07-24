from typing import Any, List

from multiversx_sdk_network_providers.proxy_network_provider import \
    ProxyNetworkProvider

from multiversx_sdk_cli import cli_shared, errors, utils
from multiversx_sdk_cli.delegation import staking_provider
from multiversx_sdk_cli.transactions import do_prepare_transaction


def setup_parser(args: List[str], subparsers: Any) -> Any:
    parser = cli_shared.add_group_subparser(subparsers, "staking-provider", "Staking provider omnitool")
    subparsers = parser.add_subparsers()

    # create new delegation contract
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "create-new-delegation-contract",
                                           "Create a new delegation system smart contract, transferred value must be"
                                           "greater than baseIssuingCost + min deposit value")
    _add_common_arguments(args, sub)
    sub.add_argument("--total-delegation-cap", required=True, help="the total delegation contract capacity")
    sub.add_argument("--service-fee", required=True, help="the delegation contract service fee")
    sub.set_defaults(func=do_create_delegation_contract)

    # get contract address
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "get-contract-address",
                                           "Get create contract address by transaction hash")
    sub.add_argument("--create-tx-hash", required=True, help="the hash")
    sub.add_argument("--sender", required=False, help="the sender address")
    cli_shared.add_proxy_arg(sub)
    sub.set_defaults(func=get_contract_address_by_deploy_tx_hash)

    # add a new node
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "add-nodes",
                                           "Add new nodes must be called by the contract owner")
    sub.add_argument("--validators-file", required=True, help="a JSON file describing the Nodes")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    sub.add_argument("--using-delegation-manager", action="store_true", required=False, help="whether delegation contract was created using the Delegation Manager")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=add_new_nodes)

    # remove nodes
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "remove-nodes",
                                           "Remove nodes must be called by the contract owner")
    sub.add_argument("--bls-keys", required=True, help="a list with the bls keys of the nodes")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=remove_nodes)

    # stake nodes
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "stake-nodes",
                                           "Stake nodes must be called by the contract owner")
    sub.add_argument("--bls-keys", required=True, help="a list with the bls keys of the nodes")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=stake_nodes)

    # unbond nodes
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "unbond-nodes",
                                           "Unbond nodes must be called by the contract owner")
    sub.add_argument("--bls-keys", required=True, help="a list with the bls keys of the nodes")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=unbond_nodes)

    # unstake nodes
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "unstake-nodes",
                                           "Unstake nodes must be called by the contract owner")
    sub.add_argument("--bls-keys", required=True, help="a list with the bls keys of the nodes")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=unstake_nodes)

    # unjail nodes
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "unjail-nodes",
                                           "Unjail nodes must be called by the contract owner")
    sub.add_argument("--bls-keys", required=True, help="a list with the bls keys of the nodes")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=unjail_nodes)

    # change service fee
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "change-service-fee",
                                           "Change service fee must be called by the contract owner")
    sub.add_argument("--service-fee", required=True, help="new service fee value")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=change_service_fee)

    # modify total delegation cap
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "modify-delegation-cap",
                                           "Modify delegation cap must be called by the contract owner")
    sub.add_argument("--delegation-cap", required=True, help="new delegation contract capacity")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=modify_delegation_cap)

    # set automatic activation
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "automatic-activation",
                                           "Automatic activation must be called by the contract owner")

    sub.add_argument("--set", action="store_true", required=not (utils.is_arg_present(args, "--unset")),
                     help="set automatic activation True")
    sub.add_argument("--unset", action="store_true", required=not (utils.is_arg_present(args, "--set")),
                     help="set automatic activation False")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=automatic_activation)

    # set redelegate cap
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "redelegate-cap",
                                           "Redelegate cap must be called by the contract owner")

    sub.add_argument("--set", action="store_true", required=not (utils.is_arg_present(args, "--unset")),
                     help="set redelegate cap True")
    sub.add_argument("--unset", action="store_true", required=not (utils.is_arg_present(args, "--set")),
                     help="set redelegate cap False")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=redelegate_cap)

    # set metadata
    sub = cli_shared.add_command_subparser(subparsers, "staking-provider", "set-metadata",
                                           "Set metadata must be called by the contract owner")

    sub.add_argument("--name", required=True, help="name field in staking provider metadata")
    sub.add_argument("--website", required=True, help="website field in staking provider metadata")
    sub.add_argument("--identifier", required=True, help="identifier field in staking provider metadata")
    sub.add_argument("--delegation-contract", required=True, help="address of the delegation contract")
    _add_common_arguments(args, sub)
    sub.set_defaults(func=set_metadata)


def _add_common_arguments(args: List[str], sub: Any):
    cli_shared.add_proxy_arg(sub)
    cli_shared.add_wallet_args(args, sub)
    cli_shared.add_tx_args(args, sub, with_receiver=False, with_data=False, with_estimate_gas=True, with_guardian=True)
    cli_shared.add_broadcast_args(sub, relay=False)
    cli_shared.add_outfile_arg(sub, what="signed transaction, hash")
    cli_shared.add_guardian_wallet_args(args, sub)


def do_create_delegation_contract(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_for_create_new_staking_contract(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def get_contract_address_by_deploy_tx_hash(args: Any):
    args = utils.as_object(args)

    proxy = ProxyNetworkProvider(args.proxy)

    transaction = proxy.get_transaction(args.create_tx_hash)
    transaction_events = transaction.logs.events
    if len(transaction_events) == 1:
        contract_address = transaction_events[0].address
        print(contract_address.bech32())
    else:
        raise errors.ProgrammingError("Tx has more than one event. Make sure it's a staking provider SC Deploy transaction.")


def add_new_nodes(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_for_add_nodes(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def remove_nodes(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_for_remove_nodes(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def stake_nodes(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_for_stake_nodes(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def unbond_nodes(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_for_unbond_nodes(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def unstake_nodes(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_for_unstake_nodes(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def unjail_nodes(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_for_unjail_nodes(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def change_service_fee(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_change_service_fee(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def modify_delegation_cap(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_modify_delegation_cap(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def automatic_activation(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_automatic_activation(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def redelegate_cap(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_redelegate_cap(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)


def set_metadata(args: Any):
    cli_shared.check_guardian_and_options_args(args)
    cli_shared.check_broadcast_args(args)
    cli_shared.prepare_nonce_in_args(args)
    cli_shared.prepare_chain_id_in_args(args)
    staking_provider.prepare_args_set_metadata(args)
    tx = do_prepare_transaction(args)

    cli_shared.send_or_simulate(tx, args)
