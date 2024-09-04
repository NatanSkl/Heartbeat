import os

from harmony.monitors import (ConvertToPdfMonitor, IsSearchableMonitor, SplitPdfMonitor, DocumentAiMonitor,
                              AzureDiMonitor, RhythmMonitor, CombinePdfMonitor, CombineLsdMonitor)
from melod.monitors import MelodMonitor


def run_monitors(verbose=False):
    credentials = {
        "test": {
            "username": os.getenv("STORAGE_ACCOUNT"),
            "key": os.getenv("STORAGE_ACCOUNT_KEY"),
        },
        "prod": {
            "username": os.getenv("STORAGE_ACCOUNT_PROD"),
            "key": os.getenv("STORAGE_ACCOUNT_KEY_PROD"),
        }
    }

    results = {}

    for env, creds in credentials.items():
        username = creds["username"]
        key = creds["key"]

        harmony_monitors = [ConvertToPdfMonitor(username, key), IsSearchableMonitor(username, key),
                            SplitPdfMonitor(username, key), DocumentAiMonitor(username, key),
                            AzureDiMonitor(username, key), RhythmMonitor(username, key),
                            CombinePdfMonitor(username, key), CombineLsdMonitor(username, key)]

        melod_monitors = [MelodMonitor(username, key)]

        env = "test" if username == "sagoledev" else "prod"
        for monitor in harmony_monitors:
            monitor.check_pulses(env)
            results[(type(monitor).__name__, env)] = monitor.pulse_errors
            if verbose:
                print(type(monitor).__name__)
                print(env)
                print(monitor.pulse_errors)
                print("---")

        for monitor in melod_monitors:
            monitor.check_pulses(None)
            results[(type(monitor).__name__, 'melod')] = monitor.pulse_errors
            if verbose:
                print(type(monitor).__name__)
                print(env)
                print(monitor.pulse_errors)
                print("---")

    return results


if __name__ == "__main__":
    """
    Setup:
        - run harmony/set_env_variables_server.sh
        - set STORAGE_ACCOUNT, STORAGE_ACCOUNT_KEY env variables (test credentials)
        - set STORAGE_ACCOUNT_PROD, STORAGE_ACCOUNT_KEY_PROD env variables (prod credentials)
    """
    results = run_monitors(verbose=True)
    print("Monitor Results:")
    for (monitor_type, env), errors in results.items():
            print(f"Monitor: {monitor_type}, Environment: {env}")
            print("Errors:", errors)
            print("---")
