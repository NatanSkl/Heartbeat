import os
import requests
from monitoring import Monitor, PulseError
from blobs import BlobManager


MONITOR_BLOB = "melod_monitoring"
MELOD_VERSION = "1.0.6.1"


class MelodMonitor(Monitor):

    def __init__(self, username, key):
        super().__init__()
        self.username = username
        self.key = key
        self.blob_manager1 = BlobManager(username, key,
                                        "ocr-microservice-output", "ocr-microservice-output")
        self.blob_manager2 = BlobManager(username, key,
                                        "melod-outputs", "melod-outputs")

    def get_address(self, target, env):
        return "https://melod-test.delightfulsky-3fe40ddd.northeurope.azurecontainerapps.io"

    def check_pulses(self, env):
        files = self.blob_manager1.list_blob(MONITOR_BLOB, container_type="input")
        lsd_files = list(filter(lambda x: x.endswith("lsd") and "_" in x, files))

        for file in lsd_files:
            display_name = file.replace('.lsd', '')
            layout_name = display_name.split("_")[0]
            new_container = f"melod_submonitor_{display_name}"

            try:
                full_path = os.path.abspath(file)
                self.blob_manager1.get_from_blob(file, file, MONITOR_BLOB)
                self.blob_manager1.put_in_blob(full_path, "ocr.lsd", new_container)
                os.remove(file)

                r = requests.get(self.get_address(None, env),
                                 json={"layout": layout_name, "version": MELOD_VERSION, "fileName": f"{new_container}.pdf",
                                       "STORAGE_ACCOUNT": self.username,
                                       "STORAGE_ACCOUNT_KEY": self.key})

                if r.ok: #r.raise_for_status()
                    output_files = self.blob_manager2.list_blob(new_container)
                    assert f"{new_container}.json" in output_files, f"MELOD didn't work for {file}"
                else:
                    assert False, f"MELOD didn't work for {file}"

                self.blob_manager2.delete_file_in_blob(f"{new_container}.json")  # TODO verify this deletes
            except Exception as e:
                pulse_error = PulseError(str(e), self.blob_manager1.storage_account)
                self.pulse_errors.append(pulse_error)
