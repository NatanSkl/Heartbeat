import os
from abc import ABC
import requests
from monitoring import Monitor, PulseError
from blobs import BlobManager


MONITOR_BLOB = "melod_monitoring"
MELOD_VERSION = "1.0.6.1"


class MelodMonitor(Monitor):

    def __init__(self,username,key):
        super().__init__()
        self.username = username
        self.key = key
        self.blob_manager1 = BlobManager(username,key,
                                        "ocr-microservice-output", "ocr-microservice-output")
        self.blob_manager2 = BlobManager(username,key,
                                        "melod-outputs", "melod-outputs")

    def get_address(self, target, env):
        return "https://melod-test.delightfulsky-3fe40ddd.northeurope.azurecontainerapps.io"

    def check_pulses(self, env):
        files = self.blob_manager1.list_blob(MONITOR_BLOB, container_type="input")
        lsd_files = list(filter(lambda x: x.endswith("lsd"), files))

        for file in lsd_files:
            lsd_name = file.replace('.lsd', '')
            new_container = f"melod_submonitor_{lsd_name}"

            try:
                full_path = os.path.abspath(file)
                path = os.path.dirname(full_path)

                self.blob_manager1.get_from_blob(file, file, MONITOR_BLOB)
                #os.rename(full_path,full_path)
                self.blob_manager1.put_in_blob(full_path, "ocr.lsd", new_container)
                os.remove(file)

                r = requests.get(self.get_address(None, env),
                                 json={"layout": lsd_name, "version": MELOD_VERSION, "fileName": f"{new_container}.pdf",
                                       "STORAGE_ACCOUNT": self.username,
                                       "STORAGE_ACCOUNT_KEY": self.key})

                r.raise_for_status()

                output_files = self.blob_manager2.list_blob(new_container)
                assert f"{new_container}.json" in output_files, "Expected output file is missing"

                self.blob_manager2.delete_file_in_blob(f"{new_container}.json")  # TODO verify this deletes
                print()

            except Exception as e:
                pulse_error = PulseError(str(e), self.blob_manager1.storage_account)
                self.pulse_errors.append(pulse_error)
