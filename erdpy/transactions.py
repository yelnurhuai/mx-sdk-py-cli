import base64
import json
import logging
from collections import OrderedDict
from typing import Any, Dict, List, TextIO

from erdpy import config, errors, utils
from erdpy.accounts import Account, Address, LedgerAccount
from erdpy.cli_password import load_password
from erdpy.interfaces import IElrondProxy, ITransaction, ITransactionOnNetwork

logger = logging.getLogger("transactions")


class Transaction(ITransaction):
    def __init__(self):
        self.hash: str = ""
        self.nonce = 0
        self.value = "0"
        self.receiver = ""
        self.sender = ""
        self.senderUsername = ""
        self.receiverUsername = ""
        self.gasPrice = 0
        self.gasLimit = 0
        self.data: str = ""
        self.chainID = ""
        self.version = 0
        self.options = 0
        self.signature = ""

    # The data field is base64-encoded. erdpy only supports utf-8 "data" at this moment.
    def data_encoded(self) -> str:
        return self._field_encoded("data")

    # Useful when loading a tx from a file (when data is already encoded in base64)
    def data_decoded(self) -> str:
        return self._field_decoded("data")

    def sender_username_encoded(self) -> str:
        return self._field_encoded("senderUsername")

    def sender_username_decoded(self) -> str:
        return self._field_decoded("senderUsername")

    def receiver_username_encoded(self) -> str:
        return self._field_encoded("receiverUsername")

    def receiver_username_decoded(self) -> str:
        return self._field_decoded("receiverUsername")

    def _field_encoded(self, field: str) -> str:
        field_bytes = self.__dict__.get(field, None).encode("utf-8")
        encoded = base64.b64encode(field_bytes).decode()
        return encoded

    def _field_decoded(self, field: str) -> str:
        return base64.b64decode(self.__dict__.get(field, None)).decode()

    def sign(self, account: Account):
        self.validate()
        self.signature = account.sign_transaction(self)

    def validate(self) -> None:
        if self.gasLimit > config.MAX_GAS_LIMIT:
            raise errors.GasLimitTooLarge(self.gasLimit, config.MAX_GAS_LIMIT)

    def serialize(self) -> bytes:
        dictionary = self.to_dictionary()
        serialized = self._dict_to_json(dictionary)
        return serialized

    def _dict_to_json(self, dictionary: Dict[str, Any]) -> bytes:
        serialized = json.dumps(dictionary, separators=(',', ':')).encode("utf8")
        return serialized

    def serialize_as_inner(self) -> str:
        inner_dictionary = self.to_dictionary_as_inner()
        serialized = self._dict_to_json(inner_dictionary)
        serialized_hex = serialized.hex()
        return f"relayedTx@{serialized_hex}"

    @classmethod
    def load_from_file(cls, f: TextIO):
        data_json: bytes = f.read().encode()
        fields = json.loads(data_json).get("tx")
        instance = cls()
        instance.__dict__.update(fields)
        instance.data = instance.data_decoded()
        instance.senderUsername = instance.sender_username_decoded()
        instance.receiverUsername = instance.receiver_username_encoded()
        return instance

    def send(self, proxy: IElrondProxy):
        if not self.signature:
            raise errors.TransactionIsNotSigned()

        logger.info(f"Transaction.send: nonce={self.nonce}")

        dictionary = self.to_dictionary()
        self.hash = proxy.send_transaction(dictionary)
        logger.info(f"Hash: {self.hash}")
        utils.log_explorer_transaction(self.chainID, self.hash)
        return self.hash

    def send_wait_result(self, proxy: IElrondProxy, timeout: int) -> ITransactionOnNetwork:
        if not self.signature:
            raise errors.TransactionIsNotSigned()

        txOnNetwork = proxy.send_transaction_and_wait_for_result(self.to_dictionary(), timeout)
        self.hash = txOnNetwork.get_hash()
        return txOnNetwork

    def to_dictionary(self) -> Dict[str, Any]:
        dictionary: Dict[str, Any] = OrderedDict()
        dictionary["nonce"] = self.nonce
        dictionary["value"] = self.value

        dictionary["receiver"] = self.receiver
        dictionary["sender"] = self.sender

        if self.senderUsername:
            dictionary["senderUsername"] = self.sender_username_encoded()
        if self.receiverUsername:
            dictionary["receiverUsername"] = self.receiver_username_encoded()

        dictionary["gasPrice"] = self.gasPrice
        dictionary["gasLimit"] = self.gasLimit

        if self.data:
            dictionary["data"] = self.data_encoded()

        dictionary["chainID"] = self.chainID

        if self.version:
            dictionary["version"] = int(self.version)

        if self.options:
            dictionary["options"] = int(self.options)

        if self.signature:
            dictionary["signature"] = self.signature

        return dictionary

    # Creates the payload for a "user" / "inner" transaction
    def to_dictionary_as_inner(self) -> Dict[str, Any]:
        dictionary = self.to_dictionary()
        dictionary["receiver"] = base64.b64encode(Address(self.receiver).pubkey()).decode()
        dictionary["sender"] = base64.b64encode(Address(self.sender).pubkey()).decode()
        dictionary["chainID"] = base64.b64encode(self.chainID.encode()).decode()
        dictionary["signature"] = base64.b64encode(bytes(bytearray.fromhex(self.signature))).decode()
        dictionary["value"] = int(self.value)

        return dictionary

    def wrap_inner(self, inner: ITransaction) -> None:
        self.data = inner.serialize_as_inner()

    def set_version(self, version: int):
        self.version = version

    def set_options(self, options: int):
        self.options = options

    def get_data(self) -> str:
        return self.data
    
    def get_hash(self) -> str:
        return self.hash


class BunchOfTransactions:
    def __init__(self):
        self.transactions: List[Transaction] = []

    def add_prepared(self, transaction: Transaction):
        self.transactions.append(transaction)

    def add(self, sender: Account, receiver_address: str, nonce: Any, value: Any, data: str, gas_price: int,
            gas_limit: int, chain: str, version: int, options: int):
        tx = Transaction()
        tx.nonce = int(nonce)
        tx.value = str(value)
        tx.receiver = receiver_address
        tx.sender = sender.address.bech32()
        tx.gasPrice = gas_price
        tx.gasLimit = gas_limit
        tx.data = data
        tx.chainID = chain
        tx.version = version
        tx.options = options

        tx.sign(sender)
        self.transactions.append(tx)

    def add_tx(self, tx):
        self.transactions.append(tx)

    def send(self, proxy: IElrondProxy):
        logger.info(f"BunchOfTransactions.send: {len(self.transactions)} transactions")
        payload = [transaction.to_dictionary() for transaction in self.transactions]
        num_sent, hashes = proxy.send_transactions(payload)
        logger.info(f"Sent: {num_sent}")
        logger.info(f"TxsHashes: {hashes}")
        return num_sent, hashes


def do_prepare_transaction(args: Any) -> Transaction:
    account = Account()
    if args.ledger:
        account = LedgerAccount(account_index=args.ledger_account_index, address_index=args.ledger_address_index)
    if args.pem:
        account = Account(pem_file=args.pem, pem_index=args.pem_index)
    elif args.keyfile:
        password = load_password(args)
        account = Account(key_file=args.keyfile, password=password)

    tx = Transaction()
    tx.nonce = int(args.nonce)
    tx.value = args.value
    tx.receiver = args.receiver
    tx.sender = account.address.bech32()
    tx.senderUsername = getattr(args, "sender_username", None)
    tx.receiverUsername = getattr(args, "receiver_username", None)
    tx.gasPrice = int(args.gas_price)
    tx.gasLimit = int(args.gas_limit)
    tx.data = args.data
    tx.chainID = args.chain
    tx.version = int(args.version)
    tx.options = int(args.options)

    tx.sign(account)
    return tx
