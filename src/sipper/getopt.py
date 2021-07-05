from dataclasses import dataclass
from string import punctuation

from sipper import Parcel


@dataclass
class Switch:
    short: str = None
    long: str = None
    alias: str = None
    takevalue: bool = False


@dataclass
class Option(Switch):
    takevalue: bool = True


nullswitch = Switch()
nullopt = Option()


def getopt(args, opts):
    # used to implicitly convert option labels to
    # parcel fields so they can be accessed naturally.
    punct_to_underscore = str.maketrans(
        punctuation, len(punctuation) * '_')

    parcel = Parcel()
    params = []

    short_map = {}
    long_map = {}
    for opt in opts:
        if isinstance(opt.short, str):
            short_map[opt.short] = opt
        if isinstance(opt.long, str):
            long_map[opt.long] = opt

    def find(mapping, label, default=None):
        try:
            return mapping[label]
        except:
            return default

    def peek(sequence, i, default=None):
        if i < len(sequence):
            return sequence[i]
        return default

    i = 0
    noopts = False
    while i < len(args):
        arg = args[i].strip()
        ahead = peek(args, i+1)
        is_final = ahead is None

        if arg == '--':
            noopts = True
        elif not noopts and arg.startswith('-'):
            is_long = arg.startswith('--')
            opt_map = long_map if is_long else short_map

            switch = arg[2:] if is_long else arg[1:]
            pair = switch.split('=')
            label = pair[0]
            desc = find(opt_map, label, nullopt)
            alias = None

            if desc.alias is not None:
                alias = desc.alias
            else:
                if desc.long is not None:
                    alias = desc.long
                else:
                    alias = label
                # replace any dashes with underscores so that
                # implicit properties can still be 
                alias = alias.translate(punct_to_underscore)

            if len(pair) >= 2:
                parcel[alias] = pair[1]
            elif not is_final and \
                 not ahead.startswith('-') and \
                 desc.takevalue:
                i += 1
                parcel[alias] = ahead
            else:
                parcel[alias] = True
        else:
            params.append(arg)

        i += 1

    return parcel, params