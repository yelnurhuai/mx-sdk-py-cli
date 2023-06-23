import logging
from pathlib import Path
from typing import Any, List, Tuple, Union

from multiversx_sdk_core import Address, ArbitraryMessage
from multiversx_sdk_wallet.validator_pem import ValidatorPEM
from multiversx_sdk_wallet.validator_signer import ValidatorSigner

from multiversx_sdk_cli import utils
from multiversx_sdk_cli.accounts import Account
from multiversx_sdk_cli.cli_password import load_password
from multiversx_sdk_cli.config import (GAS_PER_DATA_BYTE, MIN_GAS_LIMIT,
                                       MetaChainSystemSCsCost)
from multiversx_sdk_cli.contracts import SmartContract
from multiversx_sdk_cli.errors import BadUsage
from multiversx_sdk_cli.validators.validators_file import ValidatorsFile

logger = logging.getLogger("validators")

VALIDATORS_SMART_CONTRACT_ADDRESS = "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqplllst77y4l"


def prepare_args_for_stake(args: Any):
    if args.top_up:
        prepare_args_for_top_up(args)
        return

    if args.pem:
        node_operator = Account(pem_file=args.pem)
    elif args.keyfile:
        password = load_password(args)
        node_operator = Account(key_file=args.keyfile, password=password)
    else:
        raise BadUsage("cannot initialize node operator")

    validators_file_path = Path(args.validators_file)
    reward_address = Address.from_bech32(args.reward_address) if args.reward_address else None

    data, gas_limit = prepare_transaction_data_for_stake(node_operator.address, validators_file_path, reward_address)
    args.data = data
    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS

    if args.estimate_gas:
        args.gas_limit = gas_limit


def prepare_transaction_data_for_stake(node_operator_address: Address, validators_file_path: Path, reward_address: Union[Address, None]) -> Tuple[str, int]:
    validators_file = ValidatorsFile(validators_file_path)
    num_of_nodes = validators_file.get_num_of_nodes()
    validators_list = validators_file.get_validators_list()

    call_arguments: List[Any] = []
    call_arguments.append(num_of_nodes)

    for validator in validators_list:
        # Get path of "pemFile", make it absolute
        validator_pem = Path(validator.get("pemFile")).expanduser()
        validator_pem = validator_pem if validator_pem.is_absolute() else validators_file_path.parent / validator_pem

        pem_file = ValidatorPEM.from_file(validator_pem)

        validator_signer = ValidatorSigner(pem_file.secret_key)
        message = ArbitraryMessage(bytes.fromhex(node_operator_address.hex()))

        signed_message = validator_signer.sign(message).hex()

        call_arguments.append(f"0x{pem_file.secret_key.generate_public_key().hex()}")
        call_arguments.append(f"0x{signed_message}")

    if reward_address:
        call_arguments.append(f"0x{reward_address.hex()}")

    data = SmartContract().prepare_execute_transaction_data("stake", call_arguments)
    gas_limit = estimate_system_sc_call(str(data), MetaChainSystemSCsCost.STAKE, num_of_nodes)

    return str(data), gas_limit


def prepare_args_for_top_up(args: Any):
    args.data = 'stake'
    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS

    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.STAKE, 1)


def prepare_args_for_unstake(args: Any):
    parsed_keys, num_keys = utils.parse_keys(args.nodes_public_keys)
    args.data = 'unStake' + parsed_keys
    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS

    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.UNSTAKE, num_keys)


def prepare_args_for_unbond(args: Any):
    parsed_keys, num_keys = utils.parse_keys(args.nodes_public_keys)
    args.data = 'unBond' + parsed_keys
    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS

    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.UNBOND, num_keys)


def prepare_args_for_unjail(args: Any):
    parsed_keys, num_keys = utils.parse_keys(args.nodes_public_keys)
    args.data = 'unJail' + parsed_keys
    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS

    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.UNJAIL, num_keys)


def prepare_args_for_change_reward_address(args: Any):
    reward_address = Address.from_bech32(args.reward_address)
    args.data = 'changeRewardAddress@' + reward_address.hex()
    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS

    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.CHANGE_REWARD_ADDRESS)


def prepare_args_for_claim(args: Any):
    args.data = 'claim'
    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS

    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.CLAIM)


def prepare_args_for_unstake_nodes(args: Any):
    parsed_keys, num_keys = utils.parse_keys(args.nodes_public_keys)
    args.data = 'unStakeNodes' + parsed_keys

    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.UNSTAKE, num_keys)


def prepare_args_for_unstake_tokens(args: Any):
    args.data = 'unStakeTokens'
    args.data += '@' + utils.str_int_to_hex_str(str(args.unstake_value))

    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.UNSTAKE_TOKENS)


def prepare_args_for_unbond_nodes(args: Any):
    parsed_keys, num_keys = utils.parse_keys(args.nodes_public_keys)
    args.data = 'unBondNodes' + parsed_keys

    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.UNBOND, num_keys)


def prepare_args_for_unbond_tokens(args: Any):
    args.data = 'unBondTokens'
    args.data += '@' + utils.str_int_to_hex_str(str(args.unbond_value))

    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.UNBOND_TOKENS)


def prepare_args_for_clean_registered_data(args: Any):
    args.data = 'cleanRegisteredData'

    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.STAKE)


def prepare_args_for_restake_unstaked_nodes(args: Any):
    parsed_keys, num_keys = utils.parse_keys(args.nodes_public_keys)
    args.data = 'reStakeUnStakedNodes' + parsed_keys

    args.receiver = VALIDATORS_SMART_CONTRACT_ADDRESS
    if args.estimate_gas:
        args.gas_limit = estimate_system_sc_call(args.data, MetaChainSystemSCsCost.STAKE, num_keys)


def estimate_system_sc_call(transaction_data: str, base_cost: int, factor: int = 1):
    num_bytes = len(transaction_data)
    gas_limit = MIN_GAS_LIMIT + num_bytes * GAS_PER_DATA_BYTE
    gas_limit += factor * base_cost
    return gas_limit
