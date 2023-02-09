import pytest

from multiversx_sdk_cli import errors
from multiversx_sdk_cli.accounts import Account, Address
from multiversx_sdk_cli.transactions import Transaction
from multiversx_sdk_cli.workstation import get_tools_folder


def test_address():
    address = Address("erd1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsmsgldz")
    address_cloned = Address(address)
    assert "fd691bb5e85d102687d81079dffce842d4dc328276d2d4c60d8fd1c3433c3293" == address.hex()
    assert "erd1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsmsgldz" == address.bech32()
    assert address.hex() == address_cloned.hex()
    assert address.bech32() == address_cloned.bech32()

    address = Address("fd691bb5e85d102687d81079dffce842d4dc328276d2d4c60d8fd1c3433c3293")
    address_cloned = Address(address)
    assert "fd691bb5e85d102687d81079dffce842d4dc328276d2d4c60d8fd1c3433c3293" == address.hex()
    assert "erd1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsmsgldz" == address.bech32()
    assert address.hex() == address_cloned.hex()
    assert address.bech32() == address_cloned.bech32()

    with pytest.raises(errors.EmptyAddressError):
        address = Address("")
        address.hex()

    with pytest.raises(errors.EmptyAddressError):
        address = Address("")
        address.bech32()

    with pytest.raises(errors.BadAddressFormatError):
        address = Address("bad")


def test_sign_transaction():
    alice_pem = get_tools_folder() / "testwallets" / "latest" / "users" / "alice.pem"
    alice = Account(pem_file=str(alice_pem))

    # With data
    transaction = Transaction()
    transaction.nonce = 0
    transaction.value = "0"
    transaction.sender = "erd1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsmsgldz"
    transaction.receiver = "erd188nydpkagtpwvfklkl2tn0w6g40zdxkwfgwpjqc2a2m2n7ne9g8q2t22sr"
    transaction.gasPrice = 200000000000000
    transaction.gasLimit = 500000000
    transaction.data = "foo"
    transaction.chainID = "chainID"
    transaction.version = 1
    transaction.signature = alice.sign_transaction(transaction)

    assert "0e69f27e24aba2f3b7a8842dc7e7c085a0bfb5b29112b258318eed73de9c8809889756f8afaa74c7b3c7ce20a028b68ba90466a249aaf999a1a78dcf7f4eb40c" == transaction.signature

    # Without data
    transaction = Transaction()
    transaction.nonce = 0
    transaction.value = "0"
    transaction.sender = "erd1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsmsgldz"
    transaction.receiver = "erd188nydpkagtpwvfklkl2tn0w6g40zdxkwfgwpjqc2a2m2n7ne9g8q2t22sr"
    transaction.gasPrice = 200000000000000
    transaction.gasLimit = 500000000
    transaction.data = ""
    transaction.chainID = "chainID"
    transaction.version = 1
    transaction.signature = alice.sign_transaction(transaction)

    assert "83efd1bc35790ecc220b0ed6ddd1fcb44af6653dd74e37b3a49dcc1f002a1b98b6f79779192cca68bdfefd037bc81f4fa606628b751023122191f8c062362805" == transaction.signature


def test_sign_message():
    alice_pem = get_tools_folder() / "testwallets" / "latest" / "users" / "alice.pem"
    alice = Account(pem_file=str(alice_pem))

    message = b"hello"
    signature = alice.sign_message(message)
    assert signature == "561bc58f1dc6b10de208b2d2c22c9a474ea5e8cabb59c3d3ce06bbda21cc46454aa71a85d5a60442bd7784effa2e062fcb8fb421c521f898abf7f5ec165e5d0f"
