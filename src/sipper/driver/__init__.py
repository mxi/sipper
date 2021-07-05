from dataclasses import dataclass
from typing import Any, List
from abc import ABC, abstractmethod 
from enum import Enum


class DataType(Enum):
    FRAME = 0


@dataclass
class Data:
    identifier: str
    type: DataType
    object: Any = None


@dataclass
class Info:
    recognized: bool
    properties: dict
    data: List[Data] = None


class Driver(ABC):

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def aliases(self) -> List[str]:
        pass

    @abstractmethod
    def read(self, parcel, handle, probe=False) -> Info:
        pass

    @abstractmethod
    def write(self, parcel, frames, handle) -> None:
        pass

    @abstractmethod
    def exec(self, parcel, output, input) -> None:
        pass


# TODO: temporary: probe each module in the driver packages to obtain
# a driver instance.
from sipper.driver.avs84 import AVS84Driver
from sipper.driver.excel import ExcelDriver
from sipper.driver.csv import CSVDriver


registry = [
    AVS84Driver(),
    ExcelDriver(),
    CSVDriver()
]


def find_driver(name=None, alias=None):
    if isinstance(name, str):
        lname = name.lower()
        for driver in registry:
            if driver.name.lower() == lname:
                return driver
    
    if isinstance(alias, str):
        lalias = alias.lower()
        for driver in registry:
            for dalias in driver.aliases():
                if dalias.lower() == lalias:
                    return driver

    return None