import shutil
import asyncio
import os
import sys

from azure.storage.blob.aio import BlobServiceClient


LOCAL_BLOBS = False
VERBOSE = False


class BlobManager:

    def __init__(self, storage_account, storage_key, input_container="harmony-input",
                 output_container="ocr-microservice-output"):
        if input_container == "input":
            input_container = "harmony-input"
        if output_container == "output":
            output_container = "ocr-microservice-output"
        if not LOCAL_BLOBS:
            self.storage_account = storage_account
            self.storage_key = storage_key
            self.blob_service_client = BlobServiceClient.from_connection_string(
                "DefaultEndpointsProtocol=https;AccountName=" + self.storage_account + ";AccountKey=" +
                self.storage_key + ";EndpointSuffix=core.windows.net")
            self.input_client = self.blob_service_client.get_container_client(input_container)
            self.output_client = self.blob_service_client.get_container_client(output_container)

    async def close(self):
        if not LOCAL_BLOBS:
            await asyncio.gather(self.input_client.close(), self.output_client.close(),
                                 self.blob_service_client.close())

    async def get_from_blob(self, source_path, dest_path, blob_id):
        """
        :param source_path: path inside blob
        :param dest_path: local path to download to
        :param blob_id:
        :param container: 'input' or 'output'
        :return:
        """
        if blob_id != "" and not LOCAL_BLOBS:
            blob_id += "/"
        if LOCAL_BLOBS:
            if sys.platform == "win32":
                source_path = source_path.replace("/", "\\")
            try:
                shutil.copyfile(os.path.join(blob_id, source_path), dest_path)
            except shutil.SameFileError:
                pass
        else:
            blob_client = self.input_client.get_blob_client(blob_id + source_path)

            if VERBOSE:
                print(f"Downloading {source_path}")
            with open(dest_path, "wb") as file:
                blob_stream = await blob_client.download_blob()
                file.write(await blob_stream.readall())
            if VERBOSE:
                print(f"Downloaded {source_path}")

    async def put_in_blob(self, source_path, dest_path, blob_id):
        """
        :param source_path: local path to upload
        :param dest_path: path inside blob
        :param blob_id:
        :return:
        """
        if not LOCAL_BLOBS:
            if blob_id != "":
                blob_id += "/"
            else:
                dest_path = os.path.basename(source_path.split(".")[0]) + ".pdf"
        if LOCAL_BLOBS:
            if sys.platform == "win32":
                dest_path = dest_path.replace("/", "\\")
            if os.path.dirname(dest_path) != "":
                os.makedirs(os.path.join(blob_id, os.path.dirname(dest_path)), exist_ok=True)
            else:
                os.makedirs(blob_id, exist_ok=True)
            shutil.copyfile(source_path, os.path.join(blob_id, dest_path))
        else:
            if VERBOSE:
                print(f"Uploading {source_path}")
            with open(source_path, "rb") as file:
                await self.output_client.upload_blob(name=blob_id + dest_path, data=file.read(), overwrite=True)
            if VERBOSE:
                print(f"Uploaded {source_path}")

    async def list_blob(self, blob_id, path=None):
        """
        :param blob_id:
        :param path: should be path to folder, without / at the end
        :return:
        """
        if LOCAL_BLOBS:
            if path is None:
                return os.listdir(blob_id)
            elif os.path.exists(os.path.join(blob_id, path)):
                return [f"{path}/{blob_file}" for blob_file in os.listdir(os.path.join(blob_id, path))]
            else:
                return []
        else:
            if path is None:
                iterator = self.output_client.list_blobs(blob_id)
            else:
                iterator = self.output_client.list_blobs(f"{blob_id}/{path}/")
            return [obj.name.replace(f"{blob_id}/", "") async for obj in iterator]

    async def delete_folder_in_blob(self, blob_id, folder):
        if LOCAL_BLOBS:
            shutil.rmtree(os.path.join(blob_id, folder))
        else:
            blob_files = await self.list_blob(blob_id, folder)
            for blob_file in blob_files:
                await self.output_client.delete_blob(f"{blob_id}/{blob_file}")

    async def delete_file_in_blob(self, blob_id, filename):
        if LOCAL_BLOBS:
            os.remove(os.path.join(blob_id, filename))
        else:
            await self.output_client.delete_blob(f"{blob_id}/{filename}")

    async def rename_file_in_blob(self, blob_id, old_name, new_name):
        if LOCAL_BLOBS:
            os.rename(os.path.join(blob_id, old_name), os.path.join(blob_id, old_name))
        else:
            blob_client = self.output_client.get_blob_client(f"{blob_id}/{old_name}")
            new_blob_client = self.output_client.get_blob_client(f"{blob_id}/{new_name}")
            await new_blob_client.start_copy_from_url(blob_client.url)
            await blob_client.delete_blob()
