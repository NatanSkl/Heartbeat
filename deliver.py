import requests


def post(address, params, storage_account=None, storage_key=None, input_container=None, output_container=None):
    if storage_account:
        params["storage_account"] = storage_account
    if storage_key:
        params["storage_key"] = storage_key
    if input_container:
        params["input_container"] = input_container
    if output_container:
        params["output_container"] = output_container

    return requests.post(address, json=params, headers={"Content-Type": "application/json"})