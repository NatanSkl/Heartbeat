import os

from harmony.monitors import (ConvertToPdfMonitor, IsSearchableMonitor, SplitPdfMonitor, DocumentAiMonitor, AzureDiMonitor
                    , RhythmMonitor, CombinePdfMonitor, CombineLsdMonitor)
from melod.monitors import MelodMonitor

def run_monitors():
    credentials = {
        """test": {
            "username": os.getenv("STORAGE_ACCOUNT"),
            "key": os.getenv("STORAGE_ACCOUNT_KEY"),
        },"""
        "prod": {
            "username": os.getenv("STORAGE_ACCOUNT_PROD"),
            "key": os.getenv("STORAGE_ACCOUNT_KEY_PROD"),
        }
    }

    results = {}


    for env, creds in credentials.items():
        username = creds["username"]
        key = creds["key"]

        harmony_monitors = [ConvertToPdfMonitor(username, key), IsSearchableMonitor(username, key), SplitPdfMonitor(username, key),
                            DocumentAiMonitor(username, key), AzureDiMonitor(username, key), RhythmMonitor(username, key),
                            CombinePdfMonitor(username, key), CombineLsdMonitor(username, key)]

        melod_monitors = [MelodMonitor(username, key)]

        env = "test" if username == "sagoledev" else "prod"
        for monitor in harmony_monitors:
            monitor.check_pulses(env)
            results[(type(monitor).__name__, env)] = monitor.pulse_errors
            print(type(monitor).__name__)
            print(monitor.pulse_errors)
            print("---")

        for monitor in melod_monitors:
            monitor.check_pulses(None)
            results[(type(monitor).__name__, 'melod')] = monitor.pulse_errors
            print(type(monitor).__name__)
            print(monitor.pulse_errors)
            print("---")

    return results


results = run_monitors()
print("Monitor Results:")
for (monitor_type, env), errors in results.items():
        print(f"Monitor: {monitor_type}, Environment: {env}")
        print("Errors:", errors)
        print("---")
# TODO write function that runs all monitors and returns a dict with (Monitor, env) -> errors
# TODO with Natan, copy all files to prod blobs as well




