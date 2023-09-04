import base64
import logging
from typing import Any, List, Optional, Protocol, Sequence, Tuple

from multiversx_sdk_core import Transaction, TransactionPayload
from multiversx_sdk_core.address import Address, compute_contract_address
from multiversx_sdk_network_providers.interface import IAddress, IContractQuery

from multiversx_sdk_cli import config, constants, errors
from multiversx_sdk_cli.accounts import Account, EmptyAddress
from multiversx_sdk_cli.constants import ADDRESS_ZERO_BECH32, DEFAULT_HRP
from multiversx_sdk_cli.utils import Object

logger = logging.getLogger("contracts")

HEX_PREFIX = "0x"
FALSE_STR_LOWER = "false"
TRUE_STR_LOWER = "true"
STR_PREFIX = "str:"


class INetworkProvider(Protocol):
    def query_contract(self, query: Any) -> 'IContractQueryResponse':
        ...


class QueryResult(Object):
    def __init__(self, as_base64: str, as_hex: str, as_number: Optional[int]):
        self.base64 = as_base64
        self.hex = as_hex
        self.number = as_number


class ContractQuery(IContractQuery):
    def __init__(self, address: IAddress, function: str, value: int, arguments: List[bytes], caller: Optional[IAddress] = None):
        self.contract = address
        self.function = function
        self.caller = caller
        self.value = value
        self.encoded_arguments = [item.hex() for item in arguments]

    def get_contract(self) -> IAddress:
        return self.contract

    def get_function(self) -> str:
        return self.function

    def get_encoded_arguments(self) -> Sequence[str]:
        return self.encoded_arguments

    def get_caller(self) -> Optional[IAddress]:
        return self.caller

    def get_value(self) -> int:
        return self.value


class IContractQueryResponse(Protocol):
    return_data: List[str]
    return_code: str
    return_message: str


class SmartContract:
    def __init__(self, address: Optional[IAddress] = EmptyAddress(), bytecode=None, metadata=None):
        self.address = address
        self.bytecode = bytecode
        self.metadata = metadata or CodeMetadata()

    def deploy(self, owner: Account, arguments: List[Any], gas_price: int, gas_limit: int, value: int, chain: str, version: int, guardian: str, options: int) -> Transaction:
        self.owner = owner
        self.address = compute_contract_address(self.owner.address, self.owner.nonce, DEFAULT_HRP)

        arguments = arguments or []
        gas_price = int(gas_price)
        gas_limit = int(gas_limit)
        value = value or 0

        tx = Transaction(
            chain_id=chain,
            sender=owner.address,
            receiver=Address.from_bech32(ADDRESS_ZERO_BECH32),
            gas_limit=gas_limit,
            gas_price=gas_price,
            nonce=owner.nonce,
            value=value,
            data=self.prepare_deploy_transaction_data(arguments),
            version=version,
            options=options
        )

        if guardian:
            tx.guardian = Address.from_bech32(guardian)

        tx.signature = bytes.fromhex(owner.sign_transaction(tx))
        return tx

    def prepare_deploy_transaction_data(self, arguments: List[Any]) -> TransactionPayload:
        tx_data = f"{self.bytecode}@{constants.VM_TYPE_WASM_VM}@{self.metadata.to_hex()}"

        for arg in arguments:
            tx_data += f"@{_prepare_argument(arg)}"

        return TransactionPayload.from_str(tx_data)

    def execute(self, caller: Account, function: str, arguments: List[str], gas_price: int, gas_limit: int, value: int, chain: str, version: int, guardian: str, options: int) -> Transaction:
        self.caller = caller

        arguments = arguments or []
        gas_price = int(gas_price)
        gas_limit = int(gas_limit)
        value = value or 0
        receiver = self.address if self.address else EmptyAddress()

        tx = Transaction(
            chain_id=chain,
            sender=caller.address,
            receiver=receiver,
            gas_limit=gas_limit,
            gas_price=gas_price,
            nonce=caller.nonce,
            value=value,
            data=self.prepare_execute_transaction_data(function, arguments),
            version=version,
            options=options
        )

        if guardian:
            tx.guardian = Address.from_bech32(guardian)

        tx.signature = bytes.fromhex(caller.sign_transaction(tx))
        return tx

    def prepare_execute_transaction_data(self, function: str, arguments: List[Any]) -> TransactionPayload:
        tx_data = function

        for arg in arguments:
            tx_data += f"@{_prepare_argument(arg)}"

        return TransactionPayload.from_str(tx_data)

    def upgrade(self, owner: Account, arguments: List[Any], gas_price: int, gas_limit: int, value: int, chain: str, version: int, guardian: str, options: int) -> Transaction:
        self.owner = owner

        arguments = arguments or []
        gas_price = int(gas_price or config.DEFAULT_GAS_PRICE)
        gas_limit = int(gas_limit)
        value = value or 0
        receiver = self.address if self.address else EmptyAddress()

        tx = Transaction(
            chain_id=chain,
            sender=owner.address,
            receiver=receiver,
            gas_limit=gas_limit,
            gas_price=gas_price,
            nonce=owner.nonce,
            value=value,
            data=self.prepare_upgrade_transaction_data(arguments),
            version=version,
            options=options
        )

        if guardian:
            tx.guardian = Address.from_bech32(guardian)

        tx.signature = bytes.fromhex(owner.sign_transaction(tx))
        return tx

    def prepare_upgrade_transaction_data(self, arguments: List[Any]) -> TransactionPayload:
        tx_data = f"upgradeContract@{self.bytecode}@{self.metadata.to_hex()}"

        for arg in arguments:
            tx_data += f"@{_prepare_argument(arg)}"

        return TransactionPayload.from_str(tx_data)

    def query(
        self,
        proxy: INetworkProvider,
        function: str,
        arguments: List[Any],
        value: int = 0,
        caller: Optional[Address] = None
    ) -> List[Any]:
        response_data = self.query_detailed(proxy, function, arguments, value, caller)
        return_data = response_data.return_data
        return [self._interpret_return_data(data) for data in return_data]

    def query_detailed(self, proxy: INetworkProvider, function: str, arguments: List[Any],
                       value: int = 0, caller: Optional[Address] = None) -> Any:
        arguments = arguments or []
        # Temporary workaround, until we use sdk-core's serializer.
        prepared_arguments = [bytes.fromhex(_prepare_argument(arg)) for arg in arguments]

        query = ContractQuery(self.address, function, value, prepared_arguments, caller)

        response = proxy.query_contract(query)
        # Temporary workaround, until we add "isSuccess" on the response class.
        if response.return_code != "ok":
            raise RuntimeError(f"Query failed: {response.return_message}")
        return response

    def _interpret_return_data(self, data: str) -> Any:
        if not data:
            return data

        try:
            as_bytes = base64.b64decode(data)
            as_hex = as_bytes.hex()
            as_number = _interpret_as_number_if_safely(as_hex)

            result = QueryResult(data, as_hex, as_number)
            return result
        except Exception:
            logger.warn(f"Cannot interpret return data: {data}")
            return None


def _interpret_as_number_if_safely(as_hex: str) -> Optional[int]:
    """
    Makes sure the string can be safely converted to an int (and then back to a string).

    See:
        - https://stackoverflow.com/questions/73693104/valueerror-exceeds-the-limit-4300-for-integer-string-conversion 
        - https://github.com/python/cpython/issues/95778
    """
    try:
        return int(str(int(as_hex or "0", 16)))
    except:
        return None


def _prepare_argument(argument: Any):
    as_str = str(argument)
    as_hex = _to_hex(as_str)
    return as_hex


def _to_hex(arg: str):
    if arg.startswith(HEX_PREFIX):
        return _prepare_hexadecimal(arg)

    if arg.isnumeric():
        return _prepare_decimal(arg)
    elif arg.startswith(DEFAULT_HRP):
        addr = Address.from_bech32(arg)
        return _prepare_hexadecimal(f"{HEX_PREFIX}{addr.hex()}")
    elif arg.lower() == FALSE_STR_LOWER or arg.lower() == TRUE_STR_LOWER:
        as_str = f"{HEX_PREFIX}01" if arg.lower() == TRUE_STR_LOWER else f"{HEX_PREFIX}00"
        return _prepare_hexadecimal(as_str)
    elif arg.startswith(STR_PREFIX):
        as_hex = f"{HEX_PREFIX}{arg[len(STR_PREFIX):].encode('ascii').hex()}"
        return _prepare_hexadecimal(as_hex)
    else:
        raise Exception(f"could not convert {arg} to hex")


def _prepare_hexadecimal(argument: str) -> str:
    argument = argument[len(HEX_PREFIX):]
    argument = argument.upper()
    argument = ensure_even_length(argument)

    if argument == "":
        return ""

    try:
        _ = int(argument, 16)
    except ValueError:
        raise errors.UnknownArgumentFormat(argument)
    return argument


def _prepare_decimal(argument: str) -> str:
    if not argument.isnumeric():
        raise errors.UnknownArgumentFormat(argument)

    as_number = int(argument)
    as_hexstring = hex(as_number)[len(HEX_PREFIX):]
    as_hexstring = ensure_even_length(as_hexstring)
    return as_hexstring.upper()


def ensure_even_length(string: str) -> str:
    if len(string) % 2 == 1:
        return '0' + string
    return string


def sum_flag_values(flag_value_pairs: List[Tuple[int, bool]]) -> int:
    value_sum = 0
    for value, flag in flag_value_pairs:
        if flag:
            value_sum += value
    return value_sum


class CodeMetadata:
    def __init__(self, upgradeable: bool = True, readable: bool = True, payable: bool = False, payable_by_sc: bool = False):
        self.upgradeable = upgradeable
        self.readable = readable
        self.payable = payable
        self.payable_by_sc = payable_by_sc

    def to_hex(self):
        flag_value_pairs = [
            (0x01_00, self.upgradeable),
            (0x04_00, self.readable),
            (0x00_02, self.payable),
            (0x00_04, self.payable_by_sc)
        ]
        metadata_value = sum_flag_values(flag_value_pairs)
        return f"{metadata_value:04X}"
