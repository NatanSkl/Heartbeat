import os
from abc import ABC
import requests
from monitoring import Monitor, PulseError
from blobs import BlobManager


MONITOR_BLOB = "melod_monitoring"
MELOD_VERSION = "1.0.6.1"


class MelodMonitor(Monitor):

    def __init__(self):
        self.blob_manager = BlobManager(os.getenv("STORAGE_ACCOUNT"), os.getenv("STORAGE_ACCOUNT_KEY"),
                                        "ocr-microservice-output", "melod-outputs")

    def get_address(self, target, env):
        return "https://melod-test.delightfulsky-3fe40ddd.northeurope.azurecontainerapps.io"

    def check_pulses(self, env):
        # TODO list all lsd files in MONITOR_BLOB (container_type="input")
        # TODO for each lsd file, for example, esna.lsd, copy it to f"{MONITOR_BLOB}_esna", and rename to ocr.lsd
        # TODO run requests.get to run melod, with "fileName": f"{MONITOR_BLOB}_{lsd_name}.pdf"  (<lsd_name> for esna.lsd is esna)
        # TODO list melod-outputs container and check that f"{MONITOR_BLOB}_{lsd_name}.mdma"
        # TODO later with Natan, remove files after assert


        r = requests.get(self.get_address(None, env),
                         json={"layout": "esna", "version": MELOD_VERSION, "fileName": MONITOR_BLOB + ".pdf",
                               "STORAGE_ACCOUNT": os.getenv("STORAGE_ACCOUNT"),
                               "STORAGE_ACCOUNT_KEY": os.getenv("STORAGE_ACCOUNT_KEY")})
