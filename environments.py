import asyncio
import logging
import traceback

from erdpy import errors, nodedebug

logger = logging.getLogger("environments")


class Environment:
    def __init__(self):
        pass

    def run_flow(self):
        raise NotImplementedError()

    def deploy_contract(self, contract, owner, arguments=None, gas_price=None, gas_limit=None):
        raise NotImplementedError()

    def execute_contract(self, contract, caller, function, arguments=None, gas_price=None, gas_limit=None):
        raise NotImplementedError()

    def query_contract(self, contract, function, arguments=None):
        raise NotImplementedError()

class DebugEnvironment(Environment):
    def __init__(self):
        super().__init__()

    def run_flow(self, flow):
        nodedebug.install_if_missing()
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run_node_debug_and_flow(flow))
        loop.close()
        asyncio.set_event_loop(asyncio.new_event_loop())

    async def _run_node_debug_and_flow(self, flow):
        await asyncio.wait([
            nodedebug.start_async(),
            self._wrap_flow(flow)
        ])

    async def _wrap_flow(self, flow):
        try:
            logger.debug("Wait before starting flow...")
            await asyncio.sleep(1)
            logger.debug("Starting flow...")
            flow()
            logger.debug("Flow ran.")
            await asyncio.sleep(1)
        except errors.KnownError as err:
            logger.critical(err)
        except:
            print(traceback.format_exc())
        finally:
            nodedebug.stop()

    def deploy_contract(self, contract, owner, arguments=None, gas_price=None, gas_limit=None):
        logger.debug("deploy_contract")
        tx_hash, contract_address = nodedebug.deploy(contract.bytecode, owner, arguments, gas_price, gas_limit)
        contract.address = contract_address
        return tx_hash, contract_address

    def execute_contract(self, contract, caller, function, arguments=None, gas_price=None, gas_limit=None):
        logger.debug("execute_contract")
        nodedebug.execute(contract.address, caller, function, arguments, gas_price, gas_limit)

    def query_contract(self, contract, function, arguments=None):
        logger.debug("query_contract")
        return nodedebug.query(contract.address, function, arguments)

class TestnetEnvironment(Environment):
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run_flow(self, flow):
        nodedebug.install_if_missing()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run_node_debug_and_flow(flow))
        loop.close()
        asyncio.set_event_loop(asyncio.new_event_loop())

    async def _run_node_debug_and_flow(self, flow):
        await asyncio.wait([
            nodedebug.start_async(),
            self._wrap_flow(flow)
        ])

    async def _wrap_flow(self, flow):
        try:
            logger.debug("Wait before starting flow...")
            await asyncio.sleep(1)
            logger.debug("Starting flow...")
            flow()
            logger.debug("Flow ran.")
            await asyncio.sleep(1)
        except errors.KnownError as err:
            logger.critical(err)
        except:
            print(traceback.format_exc())
        finally:
            nodedebug.stop()

    def deploy_contract(self, contract, owner, arguments=None, gas_price=None, gas_limit=None):
        logger.debug("deploy_contract")
        tx_hash, contract_address = nodedebug.deploy(contract.bytecode, owner, arguments, gas_price, gas_limit, testnet_url=self.url)
        contract.address = contract_address
        return tx_hash, contract_address

    def execute_contract(self, contract, sender, function, arguments=None, gas_price=None, gas_limit=None):
        logger.debug("execute_contract")
        nodedebug.execute(contract.address, sender, function, arguments, gas_price, gas_limit, testnet_url=self.url)

    def query_contract(self, contract, function, arguments=None):
        logger.debug("query_contract")
        return nodedebug.query(contract.address, function, arguments, testnet_url=self.url)
