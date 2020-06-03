# Configuration that should not be edited by the end user:
DOWNLOAD_MIRROR = "https://ide.elrond.com"

# Configuration that may be edited by the end user:
ROOT_FOLDER_NAME = "ElrondSCTools"

DEFAULT_GAS_PRICE = 200000000000
DEFAULT_GAS_LIMIT = 50000000
GAS_PER_DATA_BYTE = 1500
MIN_GAS_LIMIT = 50000


class MetaChainSystemSCsCost:
    STAKE = 5000000
    UNSTAKE = 5000000
    UNBOND = 5000000
    CLAIM = 5000000
    GET = 5000000
    CHANGE_REWARD_ADDRESS = 5000000
    CHANGE_VALIDATOR_KEYS = 5000000
    UNJAIL = 5000000
