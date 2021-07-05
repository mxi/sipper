import struct
from typing import IO

import pandas as pd

from sipper import Parcel
from sipper.getopt import Option
from sipper.driver import Driver, Info


class AVS84Driver(Driver):

    def name(self):
        return 'avs84'

    def version(self):
        return '0.0.0'

    def description(self):
        return 'AvaSoft 8 RAW 8 data file format'

    def aliases(self):
        return [ 'avs84', 'raw8' ]

    def cloptions(self):
        return [
            Option('avs:s', 'avs:samples', 'avs_samples'),
            Option('avs:a', 'avs:axes', 'avs_axes')
        ]

    def read(self, parcel, handle, probe=False):
        # defaults
        if not isinstance(parcel, Parcel):
            parcel = Parcel()

        if not isinstance(handle, IO):
            return None

        # header
        signature = handle.read(5).decode('ascii')
        handle.read(9)
        serial = handle.read(9).decode('ascii')
        handle.read(1)
        confirm_serial = handle.read(9).decode('ascii')
        handle.read(295)
        depth = handle.tell()

        properties = {
            'signature': signature,
            'spectrometer_serial': serial,
            'spectrometer_serial_confirm': confirm_serial,
            'header_depth': depth
        }

        recognized = (
            'AVS84'        == signature   and
            9              == len(serial) and
            confirm_serial == serial      and
            328            == depth
        )

        if not recognized or probe:
            return Info(recognized, properties)

        # TODO: figure out where sample count and column
        # count are encoded in the RAW 8 file (maybe an
        # enum related to the spectrometer serial)
        samples = 3400
        axes = 3

        # TODO: document command line options
        # TODO: read in data
        if parcel.avs_samples:
            samples = int(parcel.avs_samples)
        if parcel.avs_axes:
            axes = int(parcel.avs_axes)

        samples = max(samples, 0)
        axes = max(axes, 0)
        # 4-byte floating points per axis
        buffer_size = 4 * samples
        series = []

        for axis in range(axes):
            buffer = handle.read(buffer_size)
            size = len(buffer)
            if buffer_size != size:
                raise ValueError(
                    f'buffer size expected {buffer_size}, but was {size} on axis {axis}')
            series.append(struct.unpack(f'<{samples}f', buffer))

        data = pd.DataFrame(
            { i: s for i, s in enumerate(series) })

        return Info(recognized, properties, data)

    def write(self, parcel, frame, handle):
        raise NotImplementedError(
            'AVS84Driver.write is not supported yet.')