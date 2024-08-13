import os
from abc import ABC
import requests

from monitoring import Monitor, PulseError
from blobs import BlobManager


MONITOR_BLOB = "harmony_monitoring"


class HarmonyMonitor(Monitor, ABC):
    def __init__(self):
        super().__init__()
        self.blob_manager: BlobManager = None

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
        self.blob_manager.delete_folder_in_blob(MONITOR_BLOB, None)


class ConvertToPdfMonitor(HarmonyMonitor):
    def __init__(self):
        super().__init__()
        self.blob_manager = BlobManager(os.getenv("STORAGE_ACCOUNT"), os.getenv("STORAGE_ACCOUNT_KEY"),
                                        "harmony-input", "ocr-microservice-output")

    def test_file(self, file):
        # TODO add prod support
        address = self.get_address("CONVERT_TO_PDF", "test")
        response = requests.post(address, json={"file_path": file, "blob_id": MONITOR_BLOB}, headers={"Content-Type": "application/json"})
        files = self.blob_manager.list_blob(MONITOR_BLOB)
        assert("in.pdf" in files, f"Couldn't CONVERT_TO_PDF the file: {file}")

    def check_pulses(self):
        files = self.blob_manager.list_blob(MONITOR_BLOB, container_type="input")
        cvt_files = list(filter(lambda x: x.startswith("cvt"), files))
        for file in cvt_files:
            try:
                self.test_file(file)
                self.clear_blob()
            except Exception as e:
                print(e)
                pulse_error = PulseError(str(e), self.blob_manager.storage_account)
                self.pulse_errors.append(pulse_error)
