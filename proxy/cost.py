import base64
import logging

from erdpy.proxy.tx_types import TxTypes
from erdpy import utils, errors
from erdpy.projects import load_project

logger = logging.getLogger("proxy")


class TransactionCostEstimator:
    # needs these constant because when the observer node receive a post request from proxy with a transaction needs
    # to can figure out what type of transaction was send to can calculate an estimation
    _SENDER_ADDRESS = "e3784da068cca901c0c629b304d024eb777fdf604dd8f6b5c0dc0c7f75877473"
    _RECEIVER_ADDRESS = "e3784da068cca901c0c629b304d024eb777fdf604dd8f6b5c0dc0c7f75877471"

    def __init__(self, proxy_url):
        self.proxy_url = proxy_url

    def estimate_tx_cost(self, arguments):
        tx_type = arguments.tx_type

        if tx_type == TxTypes.MOVE_BALANCE:
            self._estimate_move_balance(arguments.data)
        elif tx_type == TxTypes.SC_DEPLOY:
            self._estimate_sc_deploy(arguments.sc_path)
        else:
            self._estimate_sc_call(arguments.sc_address, arguments.function, arguments.arguments)

    def _estimate_move_balance(self, data):
        sender = self._SENDER_ADDRESS
        receiver = self._RECEIVER_ADDRESS
        data = data or ""
        data_bytes = base64.b64encode(data.encode())

        self._send_transaction(sender, receiver, data_bytes.decode())

    def _estimate_sc_deploy(self, contract_path):
        if contract_path is None:
            logger.fatal("contract-path argument missing")
            return

        project = load_project(contract_path)
        bytecode = project.get_bytecode()

        base64_bytecode = base64.b64encode(bytecode.encode())

        sender = self._SENDER_ADDRESS
        receiver = self._RECEIVER_ADDRESS
        self._send_transaction(sender, receiver, base64_bytecode.decode())

    def _estimate_sc_call(self, sc_address, function, arguments):
        if function is None:
            logger.fatal("function argument missing")
            return

        if sc_address is None:
            logger.fatal("sc-address argument missing")
            return

        sender = self._SENDER_ADDRESS
        receiver = sc_address
        arguments = arguments or []
        tx_data = function
        for arg in arguments:
            tx_data += f"@{prepare_argument(arg)}"

        base64_bytes = base64.b64encode(tx_data.encode())
        self._send_transaction(sender, receiver, base64_bytes.decode())

    def _send_transaction(self, sender, receiver, data):
        tx_object = {
            "nonce": 1,
            "value": "0",
            "receiver": receiver,
            "sender": sender,
            "data": data
        }
        url = f"{self.proxy_url}/transaction/cost"

        raw_response = utils.post_json(url, tx_object)
        gas_units_key = 'txGasUnits'
        if gas_units_key in raw_response.keys():
            print(raw_response[gas_units_key])
            return

        print(raw_response)
