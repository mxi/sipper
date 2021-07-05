import os
import sys
import struct

import pandas as pd

from sipper import getelse 
from sipper.getopt import Option, Switch, getopt 


__version__ = '0.0.5-dev'

terse = \
f"""
sipper - a data file format converter.
usage: sipper [OPTIONS] [<input>...]
       sipper --help
       sipper --manual

OPTIONS
    -v, --version                  Display version information and exit.
    -o, --output                   Specify the output file or directory.
    -avs:s, --avs:samples          Manually specify AVS84 sample count.
    -avs:d, --avs:dimensions       Manually specify AVS84 axis count.
    -i, --write-index              Enable row indices in output files.
    -h, --write-header             Enable column labels in output files.
    -y, --override                 Override any existing input.
    -x, --excel-sheet              Write data to individual 
                                       spreadsheets.
    -X, --excel-book               Write data to a single spreadsheet
                                       with a sheet per input file.
    -c, --csv                      Write data to individual CSV files.

    --help                         Display this terse help page.
    --manual                       Display the complete manual page.

VERSION
    sipper {__version__}

AUTHOR
    Originally developed by Maxim Kasyanenko. Licensed under GPLv3
    (https://www.gnu.org/licenses/gpl-3.0.en.html).

    Contribute to the development at https://github.com/mxi/sipper.
"""

manual = \
f"""
sipper - a data file format converter.
usage: sipper [OPTIONS] [<input>...]
       sipper --help
       sipper --manual

DESCRIPTION
    Akin to a software swiss army knife which converts often proprietary
    data files to different, more standardized formats such as Excel
    spreadsheets and CSV.

EXAMPLES
    sipper -x file
        Convert 'file' in the current working directory into a
        spreadsheet file in the same directory with the same name.

    sipper -x *
        Convert all items (*) in the current working directory into
        individual spreadsheets in the same directory.

    sipper -i -h -c -o out measure/*
        Convert all items in the 'measure' directory (measure/*) into
        individual CSV files (-c) with row indices (-i) and column 
        labels (-h), and write the results into the 'out' directory
        (-o out).

    sipper -i -h -y -c -x -X -o out/ *
        Convert all items (*) in the current working directory into 
        CSV (-c), separate spreadsheets (-x), and coalesced spreadsheet 
        (-X) with row indces (-i) and column labels (-h), and output the 
        results into the out/ directory (-o out/) without regard to
        existing files (-y).

OPTIONS
    -v, --version
        Display version information and exit.

    -avs:s, --avs:samples
        Manually set the number of samples in any input AvaSoft RAW 8
        (AVS84, raw8) files.

    -avs:d, --avs:dimensions
        Manually set the number of dimensions (axes) in any input
        AvaSoft RAW 8 (AVS84, raw8) files.

    -i, --write-index
        Export a row index column in the resulting output files.

    -h, --write-header
        Export column labels in the resulting output files.

    -y, --override
        Override any existing files with the new output files.

    -x, --excel-sheet
        Convert input data into individual Excel workbooks. Each sheet 
        within each output workbook has a name reflecting that of the
        corresponding input file.

    -X, --excel-book
        Convert input data into a single, coalesched Excel workbook with
        a separate sheet for each individual input file. Each sheet's
        name is reflective of the corresponding input file name.

    -c, --csv
        Convert input data into individual comma-separated values (CSV)
        files.

    --help
        Display the terse manual and exit.

    --manual
        Display this manual and exit.

VERSION
    sipper {__version__}

AUTHOR
    Originally developed by Maxim Kasyanenko. Licensed under GPLv3
    (https://www.gnu.org/licenses/gpl-3.0.en.html).

    Contribute to the development at https://github.com/mxi/sipper.
"""


def strip_extension(file_name):
    split = file_name.split('.')
    if 1 < len(split):
        return ''.join(file_name.split('.')[:-1])
    return split[0]


def load_avs84(parcel, path, probe=False):
    with open(path, 'rb') as fin:
        # header
        signature = fin.read(5).decode('ascii')
        fin.read(9)
        serial = fin.read(9).decode('ascii')
        fin.read(1)
        confirm_serial = fin.read(9).decode('ascii')
        fin.read(295)
        header_depth = fin.tell()

        # TODO: figure out where sample count and column
        # count are encoded in the RAW 8 file (maybe an
        # enum related to the spectrometer serial)
        samples = 3400
        dimensions = 3

        # TODO: document command line options
        # TODO: read in data
        if parcel.avs_samples:
            samples = int(parcel.avs_samples)
        if parcel.avs_dimensions:
            dimensions = int(parcel.avs_dimensions)

        samples = max(samples, 0)
        dimensions = min(max(dimensions, 0), 3)

        properties = {
            'signature': signature,
            'spectrometer_serial': serial,
            'spectrometer_serial_confirm': confirm_serial,
            'sample_count': samples,
            'dimension_count': dimensions,
            'header_depth': header_depth
        }

        recognized = (
            'AVS84'        == signature   and
            9              == len(serial) and
            confirm_serial == serial      and
            328            == header_depth
        )

        if probe:
            return properties, recognized

        if not recognized:
            raise ValueError(f'AVS84 (RAW 8) unrecognized in {path}')

        # 4-byte floating points per axis
        buffer_size = 4 * samples
        labels = [ 'wavelength (nm)', 'y', 'z' ]
        series = []

        for axis in range(dimensions):
            buffer = fin.read(buffer_size)
            size = len(buffer)
            if buffer_size != size:
                raise ValueError(
                    f'buffer size expected {buffer_size}, but was {size} on axis {axis}')
            series.append(struct.unpack(f'<{samples}f', buffer))

        file_depth = fin.tell()
        properties['file_depth'] = file_depth

        return properties, pd.DataFrame({ l: s for l, s in zip(labels, series) })


def probe_avs84_only(parcel, files):
    avs84_inputs = []
    for input in files:
        try:
            _, recognized = load_avs84(parcel, input, probe=True)
            if recognized:
                avs84_inputs.append(input)
            else:
                print(f'warn: {input} not an AVS84 file')
        except Exception as e:
            sys.stderr.write(f'error({type(e).__name__}): {e}\n')
    return avs84_inputs


def do_injective_mapping(parcel, params, extension, callback):
    # probe input files for AVS84
    avs84_inputs = probe_avs84_only(parcel, params)
    if 0 == len(avs84_inputs):
        sys.stderr.write(
            f'critical: no input files passed AVS84 probe check.\n')
        return

    # convert
    multiple_inputs = 1 < len(avs84_inputs)
    for input in avs84_inputs:
        name = strip_extension(os.path.basename(input))
        output = parcel.output
        if output is None:
            output = os.path.dirname(input)

        if 0 == len(output):
            output = os.getcwd()

        parent = os.path.dirname(output)
        try:
            if 0 < len(parent) and not os.path.exists(parent):
                os.makedirs(parent)
            if (not os.path.exists(output) or 
                not os.path.isdir(output)) and multiple_inputs:
                os.makedirs(output)
        except Exception as e:
            sys.stderr.write(f'fatal({type(e).__name__}): {e}\n')
            sys.stderr.write('cannot create output directory\n')
            break

        if os.path.isdir(output):
            output = os.path.join(
                output, strip_extension(name) + '.' + extension)

        if os.path.exists(output) and not parcel.override:
            sys.stderr.write(
                f'error: {output} already exists, aborting conversion of {input}\n')
            sys.stderr.write('use: -y to override existing files\n')
            continue

        try:
            properties, data = load_avs84(parcel, input)
            callback(data, output, name)
            print(f'{input} -> {output}')
            for k, v in properties.items():
                print(f'\t{k}: {v}')
        except Exception as e:
            sys.stderr.write(f'error({type(e).__name__}): {e}\n')
            continue


def do_excel_sheet(parcel, params):
    do_injective_mapping(parcel, params, 'xlsx',
        lambda data, file, srcname: pd.DataFrame.to_excel(data, file,
            index=getelse(parcel, 'write_index', False),
            header=getelse(parcel, 'write_header', False),
            sheet_name=srcname
        )
    )

def do_csv(parcel, params):
    do_injective_mapping(parcel, params, 'csv',
        lambda data, file, _: pd.DataFrame.to_csv(data, file,
            index=getelse(parcel, 'write_index', False),
            header=getelse(parcel, 'write_header', False),
        )
    )

def do_excel_book(parcel, params):
    # probe input files for AVS84
    avs84_inputs = probe_avs84_only(parcel, params)
    if 0 == len(avs84_inputs):
        sys.stderr.write(
            f'critical: no input files passed AVS84 probe check.\n')
        return

    output = parcel.output
    if output is None:
        output = os.path.dirname(avs84_inputs[0])

    if 0 == len(output):
        output = os.getcwd()

    parent = os.path.dirname(output)
    try:
        if 0 < len(parent) and not os.path.exists(parent):
            os.makedirs(parent)
    except Exception as e:
        sys.stderr.write(f'fatal({type(e).__name__}): {e}')
        sys.stderr.write('cannot create output directory')
        return
    
    if os.path.isdir(output):
        output = os.path.join(output, 'out.xlsx')
        print(f'warn: output file not specified, using {output}')

    if os.path.exists(output) and not parcel.override:
        sys.stderr.write(
            f'error: {output} already exists, aborting conversion process\n')
        sys.stderr.write('use: -y to override existing files\n')
        return

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for input in avs84_inputs:
            name = strip_extension(os.path.basename(input))
            try:
                properties, data = load_avs84(parcel, input)
                data.to_excel(writer, 
                    index=getelse(parcel, 'write_index', False),
                    header=getelse(parcel, 'write_header', True),
                    sheet_name=name
                )
                print(f'{input} -> {output}')
                for k, v in properties.items():
                    print(f'\t{k}: {v}')
            except Exception as e:
                sys.stderr.write(f'error({type(e).__name__}): {e}\n')
                continue


def main():
    parcel, params = getopt(sys.argv[1:], [
        Switch('v'    , 'version'       ),
        Option('o'    , 'output'        ),

        Option('avs:s', 'avs:samples'   ),
        Option('avs:d', 'avs:dimensions'),

        Switch('i'    , 'write-index'   ),
        Switch('h'    , 'write-header'  ),

        Switch('y'    , 'override'      ),
        Switch('x'    , 'excel-sheet'   ),
        Switch('X'    , 'excel-book'    ),
        Switch('c'    , 'csv'           ),

        Switch(long='help'),
        Switch(long='manual')
    ])

    # dry runs
    if parcel.version:
        print(__version__)
        return

    if parcel.help:
        print(terse)
        return

    if parcel.manual:
        print(manual)
        return

    # initial checks
    if 0 == len(params):
        sys.stderr.write('no input files specified.\n')
        sys.stderr.write('see: sipper --help\n')
        return

    # execute
    executed = False
    if parcel.excel_sheet:
        do_excel_sheet(parcel, params)
        executed = True

    if parcel.excel_book:
        do_excel_book(parcel, params)
        executed = True

    if parcel.csv:
        do_csv(parcel, params)
        executed = True

    if not executed:
        sys.stderr.write('conversion format unspecified.\n')
        sys.stderr.write('see: sipper --help\n')


if __name__ == '__main__':
    main()