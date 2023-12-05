import json
from pathlib import Path
from typing import List

from multiversx_sdk_wallet import ValidatorSigner
from multiversx_sdk_wallet.validator_pem import ValidatorPEM

from multiversx_sdk_cli import guards
from multiversx_sdk_cli.errors import CannotReadValidatorsData


class ValidatorsFile:
    def __init__(self, validators_file_path: Path):
        self.validators_file_path = validators_file_path
        self._validators_data = self._read_json_file_validators()

    def get_num_of_nodes(self) -> int:
        return len(self._validators_data.get("validators", []))

    def get_validators_list(self):
        return self._validators_data.get("validators", [])

    def load_signers(self) -> List[ValidatorSigner]:
        signers: List[ValidatorSigner] = []
        for validator in self.get_validators_list():
            # Get path of "pemFile", make it absolute
            validator_pem = Path(validator.get("pemFile")).expanduser()
            validator_pem = validator_pem if validator_pem.is_absolute() else self.validators_file_path.parent / validator_pem

            pem_file = ValidatorPEM.from_file(validator_pem)

            validator_signer = ValidatorSigner(pem_file.secret_key)
            signers.append(validator_signer)

        return signers

    def _read_json_file_validators(self):
        val_file = self.validators_file_path.expanduser()
        guards.is_file(val_file)
        with open(self.validators_file_path, "r") as json_file:
            try:
                data = json.load(json_file)
            except Exception:
                raise CannotReadValidatorsData()
            return data
