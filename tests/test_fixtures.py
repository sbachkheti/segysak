import pytest
import pathlib

import numpy as np

import segyio

from segysak.segy import put_segy_texthead, get_segy_texthead, create_default_texthead

TEMP_TEST_DATA_DIR = 'test_data_temp'

TEST_SEGY_SIZE = 10
TEST_SEGY_REG = 'test_reg.segy'
TEST_SEGY_SKEW = 'test_skew.segy'

@pytest.fixture(scope="session")
def temp_dir(tmpdir_factory):
    tdir = tmpdir_factory.mktemp(TEMP_TEST_DATA_DIR)
    return pathlib.Path(str(tdir))

def create_temp_segy(n, test_file, skew=False):
    data = np.zeros((n, n, n))
    spec = segyio.spec()
    # to create a file from nothing, we need to tell segyio about the structure of
    # the file, i.e. its inline numbers, crossline numbers, etc. You can also add
    # more structural information, but offsets etc. have sensible defautls. This is
    # the absolute minimal specification for a N-by-M volume
    spec.sorting = 2
    spec.format = 1
    spec.iline = 189
    spec.xline = 193
    spec.samples = range(n)
    if skew:
        spec.ilines = range(n+n-1)
    else:
        spec.ilines = range(n)
    spec.xlines = range(n)

    xl_val = range(n+1, n+n+1, 1)
    il_val = range(1, n+1, 1)

    cdpx, cdpy = np.meshgrid(il_val, xl_val)

    if skew:
        for i, x in enumerate(cdpx):
            cdpx[i, :] = x + i

    with segyio.create(test_file, spec) as segyf:
        for i, (t, il, xl) in enumerate(zip(data.reshape(-1, n), cdpx.ravel(), cdpy.ravel())):
            segyf.header[i] = {
                    segyio.su.offset: 1,
                    189: il,
                    193: xl,
                    segyio.su.cdpx: il*1000,
                    segyio.su.cdpy: xl*1000,
                    segyio.su.ns: n
                }
            segyf.trace[i] = t
        segyf.bin.update(
            tsort=segyio.TraceSortingFormat.INLINE_SORTING,
            hdt=1000,
            mfeet=1,
            jobid=1,
            lino=1,
            reno=1,
            ntrpr=n*n,
            nart=n*n,
            fold=1
        )

    if not skew:
        put_segy_texthead(test_file, create_default_texthead())
    else:
        put_segy_texthead(test_file, create_default_texthead(override={7:'Is Skewed Test'}))

@pytest.fixture(scope="session", params=[(TEST_SEGY_SIZE, TEST_SEGY_REG, False),
                                         (TEST_SEGY_SIZE, TEST_SEGY_SKEW, True)],
                                 ids=['reg', 'skewed'])
def temp_segy(temp_dir, request):
    n, file, skew = request.param
    create_temp_segy(n, str(temp_dir/file), skew)
    return temp_dir/file