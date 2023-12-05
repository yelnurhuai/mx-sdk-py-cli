from pathlib import Path
from typing import Any, List, Protocol, Tuple

from multiversx_sdk_core import Address
from multiversx_sdk_core.transaction_factories import \
    DelegationTransactionsFactory
from multiversx_sdk_wallet import ValidatorPublicKey

from multiversx_sdk_cli.accounts import Account, LedgerAccount
from multiversx_sdk_cli.cli_password import load_password
from multiversx_sdk_cli.errors import BadUsage
from multiversx_sdk_cli.interfaces import IAddress, ITransaction
from multiversx_sdk_cli.validators.validators_file import ValidatorsFile


class IConfig(Protocol):
    chain_id: str
    min_gas_limit: int
    gas_limit_per_byte: int
    gas_limit_stake: int
    gas_limit_unstake: int
    gas_limit_unbond: int
    gas_limit_create_delegation_contract: int
    gas_limit_delegation_operations: int
    additional_gas_limit_per_validator_node: int
    additional_gas_for_delegation_operations: int


class IAccount(Protocol):
    @property
    def address(self) -> IAddress:
        ...

    nonce: int

    def sign_transaction(self, transaction: ITransaction) -> str:
        ...


class DelegationOperations:
    def __init__(self, config: IConfig) -> None:
        self._factory = DelegationTransactionsFactory(config)

    def prepare_transaction_for_new_delegation_contract(self, owner: IAccount, args: Any) -> ITransaction:
        tx = self._factory.create_transaction_for_new_delegation_contract(
            sender=owner.address,
            total_delegation_cap=int(args.total_delegation_cap),
            service_fee=int(args.service_fee),
            amount=int(args.value)
        )
        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_adding_nodes(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)
        public_keys, signed_messages = self._get_public_keys_and_signed_messages(args)

        tx = self._factory.create_transaction_for_adding_nodes(
            sender=owner.address,
            delegation_contract=delegation_contract,
            public_keys=public_keys,
            signed_messages=signed_messages
        )
        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_removing_nodes(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)
        public_keys = self._parse_public_bls_keys(args.bls_keys)

        tx = self._factory.create_transaction_for_removing_nodes(
            sender=owner.address,
            delegation_contract=delegation_contract,
            public_keys=public_keys
        )
        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_staking_nodes(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)
        public_keys = self._parse_public_bls_keys(args.bls_keys)

        tx = self._factory.create_transaction_for_staking_nodes(
            sender=owner.address,
            delegation_contract=delegation_contract,
            public_keys=public_keys
        )
        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_unbonding_nodes(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)
        public_keys = self._parse_public_bls_keys(args.bls_keys)

        tx = self._factory.create_transaction_for_unbonding_nodes(
            sender=owner.address,
            delegation_contract=delegation_contract,
            public_keys=public_keys
        )
        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_unstaking_nodes(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)
        public_keys = self._parse_public_bls_keys(args.bls_keys)

        tx = self._factory.create_transaction_for_unstaking_nodes(
            sender=owner.address,
            delegation_contract=delegation_contract,
            public_keys=public_keys
        )
        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_unjailing_nodes(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)
        public_keys = self._parse_public_bls_keys(args.bls_keys)

        tx = self._factory.create_transaction_for_unjailing_nodes(
            sender=owner.address,
            delegation_contract=delegation_contract,
            public_keys=public_keys
        )
        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_changing_service_fee(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)

        tx = self._factory.create_transaction_for_changing_service_fee(
            sender=owner.address,
            delegation_contract=delegation_contract,
            service_fee=int(args.service_fee)
        )
        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_modifying_delegation_cap(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)

        tx = self._factory.create_transaction_for_modifying_delegation_cap(
            sender=owner.address,
            delegation_contract=delegation_contract,
            delegation_cap=int(args.delegation_cap)
        )
        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_automatic_activation(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)

        if args.set:
            tx = self._factory.create_transaction_for_setting_automatic_activation(
                sender=owner.address,
                delegation_contract=delegation_contract
            )
        elif args.unset:
            tx = self._factory.create_transaction_for_unsetting_automatic_activation(
                sender=owner.address,
                delegation_contract=delegation_contract
            )
        else:
            raise BadUsage("Either `--set` or `--unset` should be provided")

        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_redelegate_cap(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)

        if args.set:
            tx = self._factory.create_transaction_for_setting_cap_check_on_redelegate_rewards(
                sender=owner.address,
                delegation_contract=delegation_contract
            )
        elif args.unset:
            tx = self._factory.create_transaction_for_unsetting_cap_check_on_redelegate_rewards(
                sender=owner.address,
                delegation_contract=delegation_contract
            )
        else:
            raise BadUsage("Either `--set` or `--unset` should be provided")

        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def prepare_transaction_for_setting_metadata(self, owner: IAccount, args: Any) -> ITransaction:
        delegation_contract = Address.new_from_bech32(args.delegation_contract)

        tx = self._factory.create_transaction_for_setting_metadata(
            sender=owner.address,
            delegation_contract=delegation_contract,
            name=args.name,
            website=args.website,
            identifier=args.identifier
        )
        tx.nonce = int(args.nonce)
        tx.version = int(args.version)
        tx.options = int(args.options)
        tx.guardian = args.guardian
        tx.signature = bytes.fromhex(owner.sign_transaction(tx))

        if args.gas_limit:
            tx.gas_limit = int(args.gas_limit)

        return tx

    def _parse_public_bls_keys(self, public_bls_keys: str) -> List[ValidatorPublicKey]:
        keys = public_bls_keys.split(",")
        validator_public_keys: List[ValidatorPublicKey] = []

        for key in keys:
            validator_public_keys.append(ValidatorPublicKey(bytes.fromhex(key)))

        return validator_public_keys

    def _get_public_keys_and_signed_messages(self, args: Any) -> Tuple[List[ValidatorPublicKey], List[bytes]]:
        validators_file_path = Path(args.validators_file).expanduser()
        validators_file = ValidatorsFile(validators_file_path)
        signers = validators_file.load_signers()

        pubkey = self._get_pubkey_to_be_signed(args)

        public_keys: List[ValidatorPublicKey] = []
        signed_messages: List[bytes] = []
        for signer in signers:
            signed_message = signer.sign(pubkey)

            public_keys.append(signer.secret_key.generate_public_key())
            signed_messages.append(signed_message)

        return public_keys, signed_messages

    def _get_pubkey_to_be_signed(self, args: Any) -> bytes:
        account = Account()
        if args.using_delegation_manager:
            account = Account(address=Address.new_from_bech32(args.delegation_contract))
        elif args.pem:
            account = Account(pem_file=args.pem)
        elif args.keyfile:
            password = load_password(args)
            account = Account(key_file=args.keyfile, password=password)
        elif args.ledger:
            account = LedgerAccount(account_index=args.ledger_account_index, address_index=args.ledger_address_index)

        return account.address.get_public_key()
