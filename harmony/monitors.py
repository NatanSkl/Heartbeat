import os
from abc import ABC
import requests
from PyPDF2 import PdfFileReader, PdfFileWriter

from monitoring import Monitor, PulseError
from blobs import BlobManager


MONITOR_BLOB = "harmony_monitoring"


class HarmonyMonitor(Monitor, ABC):
    def __init__(self):
        super().__init__()
        self.blob_manager1: BlobManager = None

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
        self.blob_manager1.delete_folder_in_blob(MONITOR_BLOB, None)


class ConvertToPdfMonitor(HarmonyMonitor):
    def __init__(self):
        super().__init__()
        self.blob_manager = BlobManager(os.getenv("STORAGE_ACCOUNT"), os.getenv("STORAGE_ACCOUNT_KEY"),
                                        "harmony-input", "ocr-microservice-output")

    def test_file(self, file):
        # TODO add prod support
        address = self.get_address("CONVERT_TO_PDF", "test")
        response = requests.post(address, json={"file_path": file, "blob_id": MONITOR_BLOB}, headers={"Content-Type": "application/json"})
        print(response.text)
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



class IsSearchable(HarmonyMonitor):
    def __init__(self):
        super().__init__()
        self.blob_manager = BlobManager(os.getenv("STORAGE_ACCOUNT"), os.getenv("STORAGE_ACCOUNT_KEY"),
                                        "harmony-input", "ocr-microservice-output")

    def check_pulses(self):
        files = self.blob_manager.list_blob(MONITOR_BLOB, container_type="input")
        is_searchable_and_non = list(filter(lambda x: x.startswith("searchable") or x.startswith("not-searchable"), files))

        for file in is_searchable_and_non:
            is_searchable = self.test_file(file)

            if is_searchable:
                assert (file.startwith("searchable") , f"The file isn't searchable -> {file}")
            else:
                assert (file.startwith("not-searchable") , f"The file searchable -> {file}")

    def test_file(self, file):
        self.blob_manager.get_from_blob(file, file, MONITOR_BLOB)
        self.blob_manager.put_in_blob(file, file, MONITOR_BLOB)
        os.remove(file)

        address = self.get_address("IS_SEARCHABLE", "test")
        response = requests.post(address, json={"file_path": file, "blob_id": MONITOR_BLOB},headers={"Content-Type": "application/json"})
        print(response.text)

        if response.ok:
            result = response.json()
            print(result)
            return result.get("result", False)
        else:
            raise Exception(f"We got a error for file ->{file}")


class Split_pdf(HarmonyMonitor):
    def __init__(self):
        super().__init__()
        self.blob_manager = BlobManager(os.getenv("STORAGE_ACCOUNT"), os.getenv("STORAGE_ACCOUNT_KEY"),
                                        "harmony-input", "ocr-microservice-output")
    def split(self,path,name_of_split):
        output_dir = os.path.join(os.getcwd(), name_of_split)
        os.makedirs(output_dir, exist_ok=True)

        pdf = PdfFileReader(path)
        for page in range(pdf.getNumPages()):
            pdf_writer = PdfFileWriter()
            pdf_writer.addPage(pdf.getPage(page))

            output = os.path.join(output_dir, f'{name_of_split}{page}.pdf')
            with open(output, 'wb') as output_pdf:
                pdf_writer.write(output_pdf)



    def check_pulses(self):
        files = self.blob_manager.list_blob(MONITOR_BLOB, container_type="input")
        for file in files:
            try:
                split_file = self.test_file(file)
                if split_file:
                    assert split_file == "split", f"The file isn't split correctly -> {file}"
            except Exception as e:
                print(e)




    def test_file(self,file):
        address = self.get_address("SPLIT_PDF", "test")
        response = requests.post(address, json={"file_path": file, "blob_id": MONITOR_BLOB},
                                 headers={"Content-Type": "application/json"})

        if response.ok:
            print(f"File {file} processed successfully.")
























