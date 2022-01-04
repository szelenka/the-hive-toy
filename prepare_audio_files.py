from os import walk, listdir
from pathlib import Path
import numpy as np
from scipy.io.wavfile import read
# ref: https://stackoverflow.com/questions/13243690/decibel-values-at-specific-points-in-wav-file
# ref: https://en.wikipedia.org/wiki/Sound_pressure#Sound_pressure_level
# import ulab as np


def relative_spl(filename: str, min_spl: float = 0.3):
    samprate, wavdata = read(filename)
    chunks = np.array_split(wavdata, wavdata.size/(samprate/10))
    print(len(chunks), len(chunks) * 0.1)
    dbs = [20*np.log10(np.sqrt(np.absolute((np.mean(chunk**2))))) for chunk in chunks]
    _min = min(dbs)
    _max = max(dbs)
    values = [(_-_min)/(_max-_min) for _ in dbs]
    return values


def relative_spl_for_files_in(directory: Path):
    for filename in [directory / _ for _ in listdir(directory) if _.endswith('.wav')]:
        _filename = filename.parent / f'{filename.stem}.csv'
        print(f'Preparing: {_filename}')
        with open(_filename, 'w') as fd:
            fd.write(','.join([f'{_:.2f}' for _ in relative_spl(filename)]))


for root, dirs, files in walk('./formatted'):
    print(root, dirs, files)
    for directory in dirs:
        relative_spl_for_files_in(Path(f'{root}/{directory}'))