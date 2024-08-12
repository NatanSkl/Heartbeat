from abc import ABC, abstractmethod


class Monitor(ABC):

    def __init__(self):
        self.errors = []

    @abstractmethod
    def get_address(self, target, env):
        pass

    @abstractmethod
    def run_tests(self):
        pass