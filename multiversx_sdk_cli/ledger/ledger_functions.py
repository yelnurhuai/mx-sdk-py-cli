import logging

from multiversx_sdk_cli.ledger.ledger_app_handler import LedgerApp

TX_HASH_SIGN_VERSION = 2
TX_HASH_SIGN_OPTIONS = 1

logger = logging.getLogger("ledger")


def do_sign_transaction_with_ledger(
        tx_payload: bytes,
        account_index: int,
        address_index: int,
        sign_using_hash: bool
) -> str:
    ledger_handler = LedgerApp()
    ledger_handler.set_address(account_index=account_index, address_index=address_index)

    logger.info("Ledger: please confirm the transaction on the device")
    signature = ledger_handler.sign_transaction(tx_payload, sign_using_hash)
    ledger_handler.close()

    return signature


def do_sign_message_with_ledger(
        message_payload: bytes,
        account_index: int,
        address_index: int
) -> str:
    ledger_handler = LedgerApp()
    ledger_handler.set_address(account_index=account_index, address_index=address_index)

    logger.info("Ledger: please confirm the message on the device")
    signature = ledger_handler.sign_message(message_payload)
    ledger_handler.close()

    return signature


def do_get_ledger_address(account_index: int, address_index: int) -> str:
    ledger_handler = LedgerApp()
    ledger_address = ledger_handler.get_address(account_index=account_index, address_index=address_index)
    ledger_handler.close()

    return ledger_address


def do_get_ledger_version() -> str:
    ledger_handler = LedgerApp()
    ledger_version = ledger_handler.get_version()
    ledger_handler.close()

    return ledger_version
