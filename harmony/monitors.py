import os
from abc import ABC
from monitoring import Monitor, PulseError
from blobs import BlobManager
import deliver


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
    def __init__(self, username, key):
        super().__init__()
        self.username = username
        self.key = key
        self.input_container = "harmony-input"
        self.output_container = "ocr-microservice-output"
        self.blob_manager = BlobManager(username, key, self.input_container, self.output_container)

    def check_pulses(self, env):
        files = self.blob_manager.list_blob(MONITOR_BLOB, container_type="input")
        cvt_files = list(filter(lambda x: x.startswith("cvt"), files))
        for file in cvt_files:
            try:
                self.test_file(file, env)
                self.clear_blob()
            except Exception as e:
                pulse_error = PulseError(str(e), self.blob_manager.storage_account)
                self.pulse_errors.append(pulse_error)

    def test_file(self, file, env):
        address = self.get_address("CONVERT_TO_PDF", env)
        params = {"file_path": file, "blob_id": MONITOR_BLOB}
        response = deliver.post(address, params, self.username, self.key, self.input_container,
                                self.output_container)
        files = self.blob_manager.list_blob(MONITOR_BLOB)
        assert "in.pdf" in files or "out.pdf" in files, f"Couldn't CONVERT_TO_PDF the file: {file}"


class IsSearchableMonitor(HarmonyMonitor):
    def __init__(self, username, key):
        super().__init__()
        self.username = username
        self.key = key
        self.input_container = "harmony-input"
        self.output_container = "ocr-microservice-output"
        self.blob_manager = BlobManager(username, key, self.input_container, self.output_container)

    def check_pulses(self, env):
        files = self.blob_manager.list_blob(MONITOR_BLOB, container_type="input")
        is_searchable_and_non = list(filter(lambda x: x.startswith("searchable") or x.startswith("not-searchable"), files))

        for file in is_searchable_and_non:
            try:
                is_searchable = self.test_file(file, env)

                if is_searchable:
                    assert file.startswith("searchable"), f"Unsearchable file got IS_SEARCHABLE true -> {file}"
                else:
                    assert file.startswith("not-searchable"), f"Seachable file got IS_SEARCHABLE false -> {file}"
                # no need for clear_blob() because IS_SEARCHABLE only returns a boolean
            except Exception as e:
                pulse_error = PulseError(str(e), self.blob_manager.storage_account)
                self.pulse_errors.append(pulse_error)

    def test_file(self, file, env):
        self.blob_manager.get_from_blob(file, file, MONITOR_BLOB)
        self.blob_manager.put_in_blob(file, file, MONITOR_BLOB)
        os.remove(file)

        address = self.get_address("IS_SEARCHABLE", env)
        params = {"file_path": file, "blob_id": MONITOR_BLOB}
        response = deliver.post(address, params, self.username, self.key, self.input_container,
                                self.output_container)

        if response.ok:
            result = response.json()
            return result.get("result", False)
        else:
            assert False, f"IS_SEARCHABLE failed for file -> {file}"


class SplitPdfMonitor(HarmonyMonitor):
    def __init__(self, username, key):
        super().__init__()
        self.username = username
        self.key = key
        self.input_container = "harmony-input"
        self.output_container = "ocr-microservice-output"
        self.blob_manager = BlobManager(username, key, self.input_container, self.output_container)

    def check_pulses(self, env):
        files = self.blob_manager.list_blob(MONITOR_BLOB, container_type="input")
        is_split = list(filter(lambda x: x.startswith("split"), files))
        for file in is_split:
            try:
                self.test_file(file)
                self.clear_blob()
            except Exception as e:
                pulse_error = PulseError(str(e), self.blob_manager.storage_account)
                self.pulse_errors.append(pulse_error)

    def test_file(self,file):
        self.blob_manager.get_from_blob(file, file, MONITOR_BLOB)
        self.blob_manager.put_in_blob(file, file, MONITOR_BLOB)
        os.remove(file)
        address = self.get_address("SPLIT_PDF", "test")

        params = {"file_path": file, "blob_id": MONITOR_BLOB, "output_folder": "pdf_parts"}
        response = deliver.post(address, params, self.username, self.key, self.input_container,
                                self.output_container)

        if response.ok:
            files = self.blob_manager.list_blob(MONITOR_BLOB, "pdf_parts", container_type="output")
            assert len(files) > 1, f"Couldn't SPLIT_PDF -> {file}"
        else:
            assert False, f"Couldn't SPLIT_PDF -> file {file}"


class EngineMonitor(HarmonyMonitor):

    def __init__(self, engine, username, key):
        super().__init__()
        self.engine = engine
        self.username = username
        self.key = key
        self.input_container = "harmony-input"
        self.output_container = "ocr-microservice-output"
        self.blob_manager = BlobManager(username, key, self.input_container, self.output_container)

    def check_pulses(self, env):
        files = self.blob_manager.list_blob(MONITOR_BLOB, container_type="input")
        try:
            # TODO fix, parent shouldn't know what RHYTHM is, instead pass a prefix parameter
            if self.engine == "RHYTHM":
                process_files = list(filter(lambda x: x.startswith("searchable"), files))
            else:
                process_files = list(filter(lambda x: x.startswith("process"), files))

            for file in process_files:
                self.test_file(file, env)
                self.clear_blob()
        except Exception as e:
            pulse_error = PulseError(str(e), self.blob_manager.storage_account)
            self.pulse_errors.append(pulse_error)

    def test_file(self, file, env):
        self.blob_manager.get_from_blob(file, file, MONITOR_BLOB)
        new_filename = file.replace("process", "").replace("searchable", "")
        self.blob_manager.put_in_blob(file, new_filename, MONITOR_BLOB)
        os.remove(file)
        address = self.get_address(self.engine, env)
        params = {"file_path": new_filename, "blob_id": MONITOR_BLOB, "output_folder": "lsd_files",
                  "output_images": False}
        response = deliver.post(address, params, self.username, self.key, self.input_container,
                                self.output_container)

        if response.ok:
            files = self.blob_manager.list_blob(MONITOR_BLOB, "lsd_files", container_type="output")
            assert len(files) > 0, f"Couldn't process file using {self.engine} -> {file}"
        else:
            assert False, f"Couldn't process file using {self.engine} -> {file}"


class DocumentAiMonitor(EngineMonitor):
    def __init__(self, username, key):
        self.username = username
        self.key = key
        super().__init__("DOCUMENTAI_PART", username, key)


class AzureDiMonitor(EngineMonitor):
    def __init__(self, username, key):
        self.username = username
        self.key = key
        super().__init__("AZUREDI_PART", username, key)


class RhythmMonitor(EngineMonitor):
    def __init__(self, username, key):
        self.username = username
        self.key = key
        super().__init__("RHYTHM", username, key)


class CombineMonitor(HarmonyMonitor):
    def __init__(self, in_type, output_name, username, key):
        super().__init__()
        self.in_type = in_type
        self.output_name = output_name
        self.username = username
        self.key = key
        self.input_container = "harmony-input"
        self.output_container = "ocr-microservice-output"
        self.blob_manager = BlobManager(username, key, self.input_container, self.output_container)

    def check_pulses(self, env):
        files = self.blob_manager.list_blob(MONITOR_BLOB, container_type="input")
        address = self.get_address(self.in_type, "test")

        try:
            # TODO fix, parent shouldn't know of children, should be passed payload key and value as params
            if self.in_type == "COMBINE_LSD":
                combine_files = list(filter(lambda x: x.endswith("lsd"), files))
                payload_key = "ocr_folders"
                payload_value = ["lsd_files"]
                folder = "lsd_files"

            else:
                combine_files = list(filter(lambda x: x.endswith("png"), files))
                payload_key = "images_folder"
                payload_value = "images"
                folder = "images"

            for file in combine_files:
                self.blob_manager.get_from_blob(file, file, MONITOR_BLOB)
                self.blob_manager.put_in_blob(file, f"{folder}/{file}", MONITOR_BLOB)
                os.remove(file)

            params = {"file_path": None, "blob_id": MONITOR_BLOB, payload_key: payload_value}
            response = deliver.post(address, params, self.username, self.key, self.input_container,
                                    self.output_container)

            if response.ok:
                files = self.blob_manager.list_blob(MONITOR_BLOB, container_type="output")
                assert self.output_name in files, f"Couldn't {self.in_type} files -> {combine_files}"
            else:
                assert False, f"Couldn't {self.in_type} files -> {combine_files}"
        except Exception as e:
            pulse_error = PulseError(str(e), self.blob_manager.storage_account)
            self.pulse_errors.append(pulse_error)

        self.clear_blob()


class CombinePdfMonitor(CombineMonitor):
    def __init__(self,username, key):
        super().__init__("COMBINE_PDF", "out.pdf", username, key)


class CombineLsdMonitor(CombineMonitor):
    def __init__(self, username, key):
        super().__init__("COMBINE_LSD", "ocr.lsd", username, key)
