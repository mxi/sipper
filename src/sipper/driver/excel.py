from sipper.getopt import Option
from sipper.driver import Driver, Info


class ExcelDriver(Driver):

    def name(self):
        pass

    def version(self):
        pass

    def description(self):
        pass

    def aliases(self):
        pass

    def cloptions(self):
        return []

    def read(self, parcel, handle, probe=False):
        pass

    def write(self, parcel, frame, handle):
        pass