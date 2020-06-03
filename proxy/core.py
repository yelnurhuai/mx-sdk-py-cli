import logging

from erdpy.proxy.http_facade import do_get, do_post

METACHAIN_ID = 4294967295
ANY_SHARD_ID = 0

logger = logging.getLogger("proxy")


class ElrondProxy:
    def __init__(self, url):
        self.url = url

    def get_account_nonce(self, address):
        url = f"{self.url}/address/{address.bech32()}"
        response = do_get(url)
        nonce = response["account"]["nonce"]
        return nonce

    def get_account_balance(self, address):
        url = f"{self.url}/address/{address.bech32()}/balance"
        response = do_get(url)
        balance = response["balance"]
        return balance

    def get_account(self, address):
        url = f"{self.url}/address/{address.bech32()}"
        response = do_get(url)
        return response

    def get_account_transactions(self, address):
        url = f"{self.url}/address/{address.bech32()}/transactions"
        response = do_get(url)
        return response

    def get_num_shards(self):
        url = f"{self.url}/network/config"
        response = do_get(url)
        num_shards_without_meta = response["message"]["config"]["erd_num_shards_without_meta"] or 0
        return num_shards_without_meta + 1

    def get_last_block_nonce(self, shard_id):
        if shard_id == "metachain":
            metrics = self._get_network_status(METACHAIN_ID)
        else:
            metrics = self._get_network_status(shard_id)

        nonce = metrics["erd_nonce"]
        return nonce

    def get_meta_nonce(self):
        url = f"{self.url}/block/meta-nonce"
        response = do_get(url)
        nonce = response["nonce"]
        return nonce

    def get_meta_block(self, nonce):
        url = f"{self.url}/block/meta/{nonce}"
        response = do_get(url)
        nonce = response["block"]
        return nonce

    def get_gas_price(self):
        metrics = self._get_network_config()
        price = metrics["erd_min_gas_price"]
        return price

    def get_chain_id(self):
        metrics = self._get_network_config()
        chain_id = metrics["erd_chain_id"]
        return chain_id

    def _get_network_status(self, shard_id):
        url = f"{self.url}/network/status/{shard_id}"
        response = do_get(url)
        details = response["message"]["status"]
        return details

    def _get_network_config(self):
        url = f"{self.url}/network/config"
        response = do_get(url)
        details = response["message"]["config"]
        return details

    def send_transaction(self, payload):
        url = f"{self.url}/transaction/send"
        response = do_post(url, payload)
        tx_hash = response["txHash"]
        return tx_hash

    def send_transactions(self, payload):
        url = f"{self.url}/transaction/send-multiple"
        response = do_post(url, payload)
        num_sent = response["numOfSentTxs"]
        hashes = response["txsHashes"]
        return num_sent, hashes

    def query_contract(self, payload):
        url = f"{self.url}/vm-values/query"
        response = do_post(url, payload)
        return response
