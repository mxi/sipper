class Parcel:

    def __init__(self, **kwargs):
        self._store = { **kwargs }

    def __iter__(self):
        return iter(self._store.items())

    def __contains__(self, name):
        return name in self._store

    def __getitem__(self, name):
       return getattr(self, name)

    def __setitem__(self, name, value):
        setattr(self, name, value)

    def __getattribute__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        try:
            return self._store[name]
        except:
            return None

    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            self._store[name] = value

    def __repr__(self):
        pair_list = ', '.join([ f'{k}={v}' for k, v in self._store.items() ])
        return f'Parcel({pair_list})'


def getelse(parcel, name, default=None):
    item = parcel[name]
    if item is None:
        return default
    return item