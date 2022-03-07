import logging
from typing import List
from erdpy import utils
from erdpy.errors import NotSupportedProjectFeature
from erdpy.projects.eei_activation import ActivationEpochsInfo
from erdpy.projects.eei_registry import EEIRegistry
from erdpy.projects.interfaces import IProject

logger = logging.getLogger("eei")

MAINNET_PROXY_URL = "https://gateway.elrond.com"
MAINNET_ENABLE_EPOCHS_URL = "https://raw.githubusercontent.com/ElrondNetwork/elrond-config-mainnet/master/enableEpochs.toml"
DEVNET_PROXY_URL = "https://devnet-gateway.elrond.com"
DEVNET_ENABLE_EPOCHS_URL = "https://raw.githubusercontent.com/ElrondNetwork/elrond-config-devnet/master/enableEpochs.toml"


def check_compatibility(project: IProject):
    if _should_skip_checks(project):
        return

    logger.info("check_compatibility")

    wasm_file = project.get_file_wasm()
    imports_file = wasm_file.with_suffix(".imports.json")
    imports = utils.read_json_file(imports_file)

    activation_info_on_mainnet = ActivationEpochsInfo("mainnet", MAINNET_PROXY_URL, MAINNET_ENABLE_EPOCHS_URL)
    activation_info_on_devnet = ActivationEpochsInfo("devnet", DEVNET_PROXY_URL, DEVNET_ENABLE_EPOCHS_URL)
    compatible_with_mainnet = _check_imports_compatibility(imports, activation_info_on_mainnet)
    compatible_with_devnet = _check_imports_compatibility(imports, activation_info_on_devnet)

    if _should_ignore_checks(project):
        return

    if not compatible_with_mainnet or not compatible_with_devnet:
        raise NotSupportedProjectFeature()


def _should_skip_checks(project: IProject):
    return project.get_option("skip-eei-checks") is True


def _should_ignore_checks(project: IProject):
    return project.get_option("ignore-eei-checks") is True


def _check_imports_compatibility(imports: List[str], activation_info: ActivationEpochsInfo) -> bool:
    registry = EEIRegistry(activation_info)
    registry.sync_flags()

    not_active: List[str] = []
    not_active_maybe: List[str] = []

    for function_name in imports:
        is_active = registry.is_function_active(function_name)
        if is_active is False:
            not_active.append(function_name)
        elif is_active is None:
            not_active_maybe.append(function_name)

    if not_active:
        logger.error(f"This project requires functionality not yet available on *{activation_info.network_name}*: {not_active}. Use --ignore-eei-checks to ignore this error.")
    if not_active_maybe:
        logger.warn(f"This project requires functionality that may not be available on *{activation_info.network_name}*: {not_active_maybe}.")

    fully_compatible = len(not_active + not_active_maybe) == 0
    return fully_compatible
