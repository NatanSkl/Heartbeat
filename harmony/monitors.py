import os
from abc import ABC

from monitoring import Monitor
from blobs import BlobManager


class HarmonyMonitor(Monitor, ABC):
    def __init__(self):
        super().__init__()

    def get_address(self, target, env):
        if env == "local":
            return "127.0.0.1:8000"
        else:
            suffix = None
            if env == "test":
                suffix = "_TEST"
            elif env == "prod":
                suffix = ""
            else:
                raise ValueError("Invalid env parameter: " + env)
            address = "https://" + os.getenv(f"{target.upper()}_ADDRESS{suffix}") + f"/{target.lower()}"
            return address

    def clear_blob(self):
        # TODO implement
        pass


class ConvertToPdfMonitor(HarmonyMonitor):
    def __init__(self):
        super().__init__()
        self.blob_manager = BlobManager(os.getenv("STORAGE_ACCOUNT"), os.getenv("STORAGE_ACCOUNT_KEY"),
                                        "harmony-input", "ocr-microservice-output")

    def test_file(self, file):
        pass

    def run_tests(self):
        # run some file types using test_file(), if there is an error, save it
        # TODO get all files cvt starting with cvt in input container
        files = []
        for file in files:
            try:
                self.test_file(file)
                self.clear_blob()
            except Exception as e:
                self.errors.append(e)
