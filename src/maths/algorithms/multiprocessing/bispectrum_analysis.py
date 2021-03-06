#  PyMODA, a Python implementation of MODA (Multiscale Oscillatory Dynamics Analysis).
#  Copyright (C) 2019 Lancaster University
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <https://www.gnu.org/licenses/>.
import math
from typing import Tuple

from numpy import ndarray

from maths.algorithms.matlab_utils import *
from maths.algorithms.multiprocessing.time_frequency import avg_ampl_pow
from maths.num_utils import matlab_to_numpy, multi_matlab_to_numpy
from maths.params.BAParams import BAParams
from maths.signals.TimeSeries import TimeSeries
from processes.mp_utils import process


@process
def _biphase(
    sig1: TimeSeries, sig2: TimeSeries, fs: float, f0: float, fr: float, opt: dict
) -> Tuple[
    str,
    Tuple[float, float],
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
]:
    """
    Calculates biphase and biamplitude. Used in bispectrum analysis.

    :param sig1: the first signal
    :param sig2: the second signal
    :param fs:  sampling frequency
    :param f0: resolution parameter
    :param fr:
    :param opt: dictionary with params from MATLAB
    :return:
    """
    # We need to import a Matlab module such as WT, in order to be able to use "import matlab".
    import WT

    # To avoid the "import WT" being removed by the auto-import optimiser, we assign a dummy variable to it.
    dummy_variable = WT

    import matlab
    from maths.algorithms.matlabwrappers import biphase_wav_new

    name = sig1.name
    sig1list = sig1.signal.tolist()
    sig2list = sig2.signal.tolist()

    opt["PadLR1"] = matlab.double(opt["PadLR1"].tolist())
    opt["PadLR2"] = matlab.double(opt["PadLR2"].tolist())

    twf1 = [complex(i) for i in opt["twf1"]]
    twf2 = [complex(i) for i in opt["twf2"]]

    twf1r = [i.real for i in twf1]
    twf2r = [i.real for i in twf2]
    twf1i = [i.imag for i in twf1]
    twf2i = [i.imag for i in twf2]

    del opt["twf1"]
    del opt["twf2"]

    opt["twf1r"] = matlab.double(twf1r)
    opt["twf2r"] = matlab.double(twf2r)
    opt["twf1i"] = matlab.double(twf1i)
    opt["twf2i"] = matlab.double(twf2i)

    biamp1, biphase1 = biphase_wav_new.calculate(sig1list, sig1list, fs, f0, fr, opt)
    biamp2, biphase2 = biphase_wav_new.calculate(sig2list, sig2list, fs, f0, fr, opt)
    biamp3, biphase3 = biphase_wav_new.calculate(sig1list, sig2list, fs, f0, fr, opt)
    biamp4, biphase4 = biphase_wav_new.calculate(sig2list, sig1list, fs, f0, fr, opt)

    biamp1, biphase1 = multi_matlab_to_numpy(biamp1, biphase1)
    biamp2, biphase2 = multi_matlab_to_numpy(biamp2, biphase2)
    biamp3, biphase3 = multi_matlab_to_numpy(biamp3, biphase3)
    biamp4, biphase4 = multi_matlab_to_numpy(biamp4, biphase4)

    l = biamp1.shape[1]

    biamp1 = biamp1.reshape(l)
    biphase1 = biphase1.reshape(l)

    biamp2 = biamp2.reshape(l)
    biphase2 = biphase2.reshape(l)

    biamp3 = biamp3.reshape(l)
    biphase3 = biphase3.reshape(l)

    biamp4 = biamp4.reshape(l)
    biphase4 = biphase4.reshape(l)

    return (
        name,
        *fr,
        biamp1,
        biphase1,
        biamp2,
        biphase2,
        biamp3,
        biphase3,
        biamp4,
        biphase4,
    )


@process
def _bispectrum_analysis(
    sig1: TimeSeries, sig2: TimeSeries, params: BAParams
) -> Tuple[
    str,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    ndarray,
    dict,
]:
    """
    Performs bispectrum analysis.

    :param sig1: the first signal
    :param sig2: the second signal
    :param params: the params object containing parameters for the MATLAB-packaged function
    :return:
    """
    from maths.algorithms.matlabwrappers import bispec_wav_new, wav_surrogate

    name = sig1.name
    sig1 = sig1.signal
    sig2 = sig2.signal

    sig1list = sig1.tolist()
    sig2list = sig2.tolist()

    # Whether the signals are unique; if a single signal was loaded, it would have been duplicated and
    # passed to this function, making this boolean False.
    unique_signals = np.sum(np.abs(sig1 - sig2)) != 0

    fs = params.fs
    preprocess = params.preprocess

    ns = params.surr_count or 0
    nv = params.nv

    fmax = params.fmax or fs / 2
    fmin = params.fmin or math.nan
    f0 = params.f0 or 1

    params = {"nv": nv, "fmin": fmin, "fmax": fmax, "f0": f0}

    # If a unique pair of signals is being analysed, perform autobispectral and crossbispectral analysis.
    if unique_signals:

        # Note: Previously attempted to calculate bispec_wav_new in a process each. Did not work
        # due to some strange problem with the Matlab runtime. Processes would
        # hang at the `package.initialize()` stage for unknown reasons.

        print(
            "Multiple signals; performing autobispectral and crossbispectral analysis..."
        )
        bispxxx, _, _, _, _ = bispec_wav_new.calculate(sig1list, sig1list, fs, params)
        bispppp, _, _, _, _ = bispec_wav_new.calculate(sig2list, sig2list, fs, params)
        bispxpp, freq, amp_wt1, amp_wt2, opt = bispec_wav_new.calculate(
            sig1list, sig2list, fs, params
        )
        bisppxx, _, _, _, _ = bispec_wav_new.calculate(sig2list, sig1list, fs, params)

        bisp_size = bispxxx.shape + (ns,)
        surrxxx = zeros(bisp_size)
        surrppp = zeros(bisp_size)
        surrxpp = zeros(bisp_size)
        surrpxx = zeros(bisp_size)

        for j in range(ns):
            surr1 = wav_surrogate.calculate(sig1list, "IAAFT2", 1)
            surr2 = wav_surrogate.calculate(sig2list, "IAAFT2", 1)

            surrxxx[:, :, j] = abs(
                bispec_wav_new.calculate(surr1, surr1, fs, params)[0]
            )
            surrppp[:, :, j] = abs(
                bispec_wav_new.calculate(surr2, surr2, fs, params)[0]
            )
            surrxpp[:, :, j] = abs(
                bispec_wav_new.calculate(surr1, surr2, fs, params)[0]
            )
            surrpxx[:, :, j] = abs(
                bispec_wav_new.calculate(surr2, surr1, fs, params)[0]
            )

    # If only one signal is being analysed, instead of a pair, perform autobispectral analysis only.
    elif not unique_signals:
        print("1 signal; performing autobispectral analysis only...")

        bispxxx, freq, amp_wt1, amp_wt2, opt = bispec_wav_new.calculate(
            sig1list, sig1list, fs, params
        )
        bispxxx = abs(bispxxx)

        if preprocess:
            # Create NaN array for WT2.
            amp_wt2 = np.empty(amp_wt1.shape)
            amp_wt2.fill(NAN)

        # Create NaN arrays for remaining bispectra.
        bisp_size = bispxxx.shape
        surr_size = bisp_size + (ns,)
        surrxxx = zeros(surr_size)

        # Create empty arrays and make them all NaN.
        bispppp = np.empty(bisp_size)
        bispxpp = np.empty(bisp_size)
        bisppxx = np.empty(bisp_size)
        surrppp = zeros(surr_size)
        surrxpp = zeros(surr_size)
        surrpxx = zeros(surr_size)
        for a in (bispppp, bispxpp, bisppxx, surrppp, surrxpp, surrpxx):
            a.fill(NAN)

        for i in range(ns):
            surr1 = wav_surrogate.calculate(sig1list, "IAAFT2", 1)

            surrxxx[:, :, i] = abs(
                bispec_wav_new.calculate(surr1, surr1, fs, params)[0]
            )

    freq = matlab_to_numpy(freq)
    avg_amp_wt1, avg_pow_wt1 = avg_ampl_pow(amp_wt1)
    avg_amp_wt2, avg_pow_wt2 = avg_ampl_pow(amp_wt2)

    pow_wt1, pow_wt2 = np.square(amp_wt1), np.square(amp_wt2)

    opt["PadLR1"] = matlab_to_numpy(opt["PadLR1"])
    opt["PadLR2"] = matlab_to_numpy(opt["PadLR2"])
    opt["twf1"] = matlab_to_numpy(opt["twf1"])
    opt["twf2"] = matlab_to_numpy(opt["twf2"])

    return (
        name,
        freq,
        amp_wt1,
        pow_wt1,
        avg_amp_wt1,
        avg_pow_wt1,
        amp_wt2,
        pow_wt2,
        avg_amp_wt2,
        avg_pow_wt2,
        bispxxx,
        bispppp,
        bispxpp,
        bisppxx,
        surrxxx,
        surrppp,
        surrxpp,
        surrpxx,
        opt,
    )
