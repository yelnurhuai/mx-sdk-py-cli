import binascii
from pathlib import Path
from typing import Any

from multiversx_sdk_core import Address, ArbitraryMessage
from multiversx_sdk_wallet.validator_pem import ValidatorPEM
from multiversx_sdk_wallet.validator_signer import ValidatorSigner

from multiversx_sdk_cli import utils
from multiversx_sdk_cli.accounts import Account
from multiversx_sdk_cli.cli_password import load_password
from multiversx_sdk_cli.config import MetaChainSystemSCsCost
from multiversx_sdk_cli.validators.core import estimate_system_sc_call
from multiversx_sdk_cli.validators.validators_file import ValidatorsFile

DELEGATION_MANAGER_SC_ADDRESS = "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqylllslmq6y6"


def prepare_args_for_create_new_staking_contract(args: Any):
    args.data = 'createNewDelegationContract'
    args.data += '@' + utils.str_int_to_hex_str(str(args.total_delegation_cap))
    args.data += '@' + utils.str_int_to_hex_str(str(args.service_fee))

    args.receiver = DELEGATION_MANAGER_SC_ADDRESS

    if args.estimate_gas:
        # factor is equals 2 because there 2 delegation manager operations when a contract is created
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.DELEGATION_MANAGER_OPS, factor=2)


def prepare_args_for_add_nodes(args: Any):
    validators_file_path = Path(args.validators_file).expanduser()
    validators_file = ValidatorsFile(validators_file_path)
    account = Account()

    # TODO: Refactor, so that only address is received here.
    if args.using_delegation_manager:
        account = Account(address=Address.from_bech32(args.delegation_contract))
    elif args.pem:
        account = Account(pem_file=args.pem)
    elif args.keyfile:
        password = load_password(args)
        account = Account(key_file=args.keyfile, password=password)

    add_nodes_data = "addNodes"
    num_of_nodes = validators_file.get_num_of_nodes()
    for validator in validators_file.get_validators_list():
        # Get path of "pemFile", make it absolute
        validator_pem = Path(validator.get("pemFile")).expanduser()
        validator_pem = validator_pem if validator_pem.is_absolute() else validators_file_path.parent / validator_pem

        pem_file = ValidatorPEM.from_file(validator_pem)

        validator_signer = ValidatorSigner(pem_file.secret_key)
        message = ArbitraryMessage(bytes.fromhex(account.address.hex()))

        signed_message = validator_signer.sign(message).hex()

        add_nodes_data += f"@{pem_file.secret_key.generate_public_key().hex()}@{signed_message}"

    args.receiver = args.delegation_contract
    args.data = add_nodes_data
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.DELEGATION_OPS, num_of_nodes + 1)


def prepare_args_for_remove_nodes(args: Any):
    _prepare_args("removeNodes", args)


def prepare_args_for_stake_nodes(args: Any):
    parsed_keys, num_keys = utils.parse_keys(args.bls_keys)
    args.data = 'stakeNodes' + parsed_keys
    args.receiver = args.delegation_contract

    if args.estimate_gas:
        cost = MetaChainSystemSCsCost.DELEGATION_OPS + MetaChainSystemSCsCost.STAKE
        args.gas_limit = estimate_system_sc_call(args.data, cost, num_keys + 1)


def prepare_args_for_unbond_nodes(args: Any):
    parsed_keys, num_keys = utils.parse_keys(args.bls_keys)
    args.data = 'unBondNodes' + parsed_keys
    args.receiver = args.delegation_contract

    if args.estimate_gas:
        cost = MetaChainSystemSCsCost.DELEGATION_OPS + MetaChainSystemSCsCost.UNBOND
        args.gas_limit = estimate_system_sc_call(args.data, cost, num_keys + 1)


def prepare_args_for_unstake_nodes(args: Any):
    parsed_keys, num_keys = utils.parse_keys(args.bls_keys)
    args.data = 'unStakeNodes' + parsed_keys
    args.receiver = args.delegation_contract

    if args.estimate_gas:
        cost = MetaChainSystemSCsCost.DELEGATION_OPS + MetaChainSystemSCsCost.UNSTAKE
        args.gas_limit = estimate_system_sc_call(args.data, cost, num_keys + 1)


def prepare_args_for_unjail_nodes(args: Any):
    _prepare_args("unJailNodes", args)


def _prepare_args(command: str, args: Any):
    parsed_keys, num_keys = utils.parse_keys(args.bls_keys)
    args.data = command + parsed_keys
    args.receiver = args.delegation_contract

    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.DELEGATION_OPS, num_keys + 1)


def prepare_args_change_service_fee(args: Any):
    data = 'changeServiceFee'
    data += '@' + utils.str_int_to_hex_str(str(args.service_fee))

    args.data = data
    args.receiver = args.delegation_contract
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.DELEGATION_OPS, 1)


def prepare_args_modify_delegation_cap(args: Any):
    data = 'modifyTotalDelegationCap'
    data += '@' + utils.str_int_to_hex_str(str(args.delegation_cap))

    args.data = data
    args.receiver = args.delegation_contract
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.DELEGATION_OPS, 1)


def prepare_args_automatic_activation(args: Any):
    data = 'setAutomaticActivation'
    if args.set:
        data += '@' + binascii.hexlify(str.encode('true')).decode()

    if args.unset:
        data += '@' + binascii.hexlify(str.encode('false')).decode()

    args.data = data
    args.receiver = args.delegation_contract
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.DELEGATION_OPS, 1)


def prepare_args_redelegate_cap(args: Any):
    data = 'setCheckCapOnReDelegateRewards'
    if args.set:
        data += '@' + binascii.hexlify(str.encode('true')).decode()

    if args.unset:
        data += '@' + binascii.hexlify(str.encode('false')).decode()

    args.data = data
    args.receiver = args.delegation_contract
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.DELEGATION_OPS, 1)


def prepare_args_set_metadata(args: Any):
    data = 'setMetaData'
    data += '@' + binascii.hexlify(str.encode(args.name)).decode()
    data += '@' + binascii.hexlify(str.encode(args.website)).decode()
    data += '@' + binascii.hexlify(str.encode(args.identifier)).decode()

    args.data = data
    args.receiver = args.delegation_contract
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.DELEGATION_OPS, 1)
