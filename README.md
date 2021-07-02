# Jeff the Sipper

> *The infamous brother of John the Ripper. The man we all
need but don't deserve. Father to murdered son, husband
to a murdered wife. And he will have his vengeance, in 
this life or the next.*

I'm not sure how well this will turn out, but the package
is intended to be the FFMPEG analog for proprietary
data file formats for highly specialized software systems,
especially those on MS Windows which commit an extraordinary
amount of sacrilege against the UNIX philosophy.

## Contributing

I would love for anyone to contribute their implementation of
a proprietary data file parser to enable users the option of
using standardized, powerful data processing tools which,
more likely than not, may overshadow the proprietary 
counterpart completely. If you feel inclined, fork the
repository, implement it, and submit a pull request. 

If you would like to implement the data parser in a
different programming language, that is completely fine,
but it would be best to integrate it into Python if at all 
possible.

## AVANTES AvaSoft 8 AVS84

My attempt to reverse engineer the AVS84 (i.e ".raw8" or RAW 
8) file format generated by the AVANTES AvaSoft 8 
spectrometer analyzer. 

My internet searches yielded quite literally nothing
regarding the structure of the AVS84 file, so the format is
hypothesized through the analysis of several such files
against their renditions into Excel, CSV, and plaintext 
through AvaSoft itself. The sole resource found regarding 
this format was by another GitHub user @padmer who also 
extracted only the parts they cared about.

### Format

As of this commit, the format currently known is as follows:

#### HEADER 

| address | type             | description              | size (bytes) |
|---------|------------------|--------------------------|--------------|
| 0x0000  | ascii-string     | "AVS84"                  | 5            |
| 0x0005  | block            | ?                        | 9            |
| 0x000e  | ascii-string     | spectrometer serial ID   | 9            |
| 0x0017  | block            | ?                        | 1            |
| 0x0018  | ascii-string     | spectrometer serial ID   | 9            |
| 0x0021  | block            | null padding?            | 3            |
| 0x0024  | block            | ?                        | 292          |

#### SERIES

| address | type             | description              | size (bytes) |
|---------|------------------|--------------------------|--------------|
| 0x0148  | f32 []           | X axis                   | 13600 ?      |
| 0x3668  | f32 []           | Y axis                   | 13600 ?      |
| 0x6b88  | f32 []           | Z axis ?                 | 13600 ?      |

#### FOOTER

| address | type             | description              | size (bytes) |
|---------|------------------|--------------------------|--------------|
| 0xa0a8  | block            | null padding?            | 13612 ?      |
| 0xd5d4  | f32              | constant `1.0f`?         | 4            |
| 0xd5d8  | block            | null padding?            | 5            |
| 0xd5dd  | block            | constant `10.0f` array?  | 1884         |
| 0xdd39  | block            | null padding?            | 1883         |

### Observations

Data is stored in little endian (LE) format with allegiance
to the IEEE-754 floating point standard.

------------------------------------------------------------
Per @padmer's implementation, the size of the data series is
clearly arbitrary, but my attempts of finding the address
related to the series size has been unsuccessful. My
presumption is that this size must be of an Int32 type
located somewhere in the HEADER.

------------------------------------------------------------
Most MYSTERY chunks are consistent accross different data
files, but the 6-byte MYSTERY chunk in the HEADER appears to
change with each file. My presumption is that it is either
a hash of the data series, or a timestamp in some encoding.
My observations noted that this MYSTERY chunk appears to
be 6 bytes in length, which is rather peculiar.