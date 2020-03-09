import logging

from erdpy.projects import load_project
from erdpy.environments import TestnetEnvironment
from erdpy.accounts import Account
from erdpy.contracts import SmartContract
from erdpy.proxy.caller import ElrondProxy
from erdpy.proxy.cost import TransactionCostEstimator

logger = logging.getLogger("examples")


def deploy_smart_contract(project_directory, owner_address, pem_file, proxy_url, arguments, gas_price, gas_limit):
    logger.debug("deploy_smart_contract")

    project = load_project(project_directory)
    bytecode = project.get_bytecode()
    contract = SmartContract(bytecode=bytecode)
    environment = TestnetEnvironment(proxy_url)
    owner = Account(owner_address, pem_file)

    def flow():
        tx, address = environment.deploy_contract(contract, owner, arguments, gas_price, gas_limit)
        logger.info("Tx hash: %s", tx)
        logger.info("Contract address: %s", address)

    environment.run_flow(flow)


def call_smart_contract(contract_address, caller_address, pem_file, proxy_url, function, arguments, gas_price,
                        gas_limit):
    logger.debug("call_smart_contract")

    contract = SmartContract(contract_address)
    environment = TestnetEnvironment(proxy_url)
    caller = Account(caller_address, pem_file)

    def flow():
        environment.execute_contract(contract, caller, function, arguments, gas_price, gas_limit)

    environment.run_flow(flow)


def query_smart_contract(contract_address, proxy_url, function, arguments):
    logger.debug("query_smart_contract")

    contract = SmartContract(contract_address)
    environment = TestnetEnvironment(proxy_url)

    def flow():
        environment.query_contract(contract, function, arguments)

    environment.run_flow(flow)


def get_account_nonce(proxy_url, address):
    logger.debug("call_get_account_nonce")

    proxy = ElrondProxy(proxy_url)
    proxy.get_account_nonce(address)


def get_account_balance(proxy_url, address):
    logger.debug("call_get_account_balance")

    proxy = ElrondProxy(proxy_url)
    proxy.get_account_balance(address)


def get_account(proxy_url, address):
    logger.debug("call_get_account")

    proxy = ElrondProxy(proxy_url)
    proxy.get_account(address)


def get_num_shards(proxy_url):
    logger.debug("call_get_number_of_shards")

    proxy = ElrondProxy(proxy_url)
    proxy.get_num_shards()


def get_last_block_nonce(proxy_url, shard_id):
    logger.debug("call_get_last_block_nonce")

    proxy = ElrondProxy(proxy_url)
    proxy.get_last_block_nonce(shard_id)


def get_gas_price(proxy_url):
    logger.debug("call_get_gas_price")

    proxy = ElrondProxy(proxy_url)
    proxy.get_gas_price()


def get_chain_id(proxy_url):
    logger.debug("call_get_chain_id")

    proxy = ElrondProxy(proxy_url)
    proxy.get_chain_id()


def get_transaction_cost(arguments):
    logger.debug("call_get_transaction_cost")

    cost_estimator = TransactionCostEstimator(arguments.proxy)
    cost_estimator.estimate_tx_cost(arguments)
