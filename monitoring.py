from abc import ABC, abstractmethod


class Monitor(ABC):

    def __init__(self):
        self.pulse_errors = []

    @abstractmethod
    def get_address(self, target, env):
        pass

    @abstractmethod
    def check_pulses(self, env):
        pass


class PulseError:
    def __init__(self, message, storage_account):
        self.message = message
        self.storage_account = storage_account

    def __repr__(self):
        return f"PulseError(message={self.message}\naccount={self.storage_account})"
