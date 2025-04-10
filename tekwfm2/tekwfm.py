# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 15:34:22 2021

@author: Pavel Gostev

WFM v.1 & v.2 reader
https://www.tek.com/sample-license
reads volts vs. time records (including fastframes) from little- and big-endian version 1 & 2 WFM files

See Also
Performance Oscilloscope Reference Waveform File Format
https://download.tek.com/manual/Waveform-File-Format-Manual-077022011.pdf

Based on
https://forum.tek.com/viewtopic.php?t=141081

Tested on Python 3.9+

"""

from struct import unpack_from as unpackf
from typing import Tuple

import numpy as np

from tekwfm2.ifaces import IScopeData, WfmMeta


class WfmReadError(Exception):
    pass


def read_wfm(path: str) -> Tuple[np.ndarray, WfmMeta]:
    """
    Reads a WFM file and returns the waveform data and metadata.

    Parameters
    ----------
    path : str
        Path to the WFM file.

    Returns
    -------
    Tuple[np.ndarray, WfmMeta]
        A tuple containing the scaled waveform data as a numpy array and the
        metadata as a WfmMeta object.

    Raises
    ------
    WfmReadError
        If the file does not conform to the expected WFM format or if any of the
        metadata checks fail.
    """
    with open(path, "rb") as f:
        hbytes = f.read(838)
        meta = decode_header(path, hbytes)

        # file signature checks
        if meta["imp_dim_count"] != 1:
            raise WfmReadError(path, "imp dim count not 1")
        if meta["exp_dim_count"] != 1:
            raise WfmReadError(path, "exp dim count not 1")
        if meta["record_type"] != 2:
            raise WfmReadError(path, "not WFMDATA_VECTOR")
        # if meta['exp_dim_1_type'] != 0:
        #    raise WfmReadError(path, 'not EXPLICIT_SAMPLE')
        if meta["time_base_1"] != 0:
            raise WfmReadError(path, "not BASE_TIME")
        if meta["fastframe"]:
            raise WfmReadError(path, "Fast Frames are not supported")
        # read curve block
        bin_wave = np.memmap(
            filename=f,
            dtype=meta["dformat"],
            mode="r",
            offset=meta["curve_offset"],
            shape=(meta["dlen"]),
            order="F",
        )

    scaled_array = bin_wave * meta["vscale"] + meta["voffset"]
    return scaled_array, meta


def decode_header(path: str, header: bytes) -> WfmMeta:
    """Decode WFM file header to obtain metadata

    Parameters
    ----------
    path : str
        Path to WFM file.
    header : bytes
        Header bytes of the file.

    Returns
    -------
    WfmMeta
        Metadata of the WFM file.
    """
    meta: WfmMeta = {}
    print(header[:10].hex())
    if len(header) != 838:
        raise WfmReadError(path, "WFM header bytes not 838")
    meta["byte_order"] = unpackf("H", header, offset=0)[0]
    if meta["byte_order"] == 0x0F0F:
        endianness = "<"  # little-endian
    elif meta["byte_order"] == 0xF0F0:
        endianness = ">"  # big-endian
    else:
        raise WfmReadError(
            path, "Endianness could not be parsed from {:4X}".format(meta["byte_order"])
        )

    meta["version"] = unpackf("8s", header, offset=2)[0]
    if meta["version"] == b":WFM#001":
        v1_offset = 2
    elif meta["version"] == b":WFM#002":
        v1_offset = 0
    else:
        raise WfmReadError(path, "Only version 1 or 2 of WFM supported in this version")

    int_format = endianness + "i"
    uint_format = endianness + "I"
    byte_format = endianness + "b"
    short_format = endianness + "h"
    double_format = endianness + "d"

    meta["imp_dim_count"] = unpackf(uint_format, header, offset=114)[0]
    meta["exp_dim_count"] = unpackf(uint_format, header, offset=118)[0]
    meta["record_type"] = unpackf(uint_format, header, offset=122)[0]
    meta["exp_dim_1_type"] = unpackf(uint_format, header, offset=244 - v1_offset)[0]
    meta["time_base_1"] = unpackf(uint_format, header, offset=768 - v1_offset)[0]
    meta["fastframe"] = unpackf(uint_format, header, offset=78)[0]
    meta["Frames"] = unpackf(uint_format, header, offset=72)[0] + 1
    meta["summary_frame"] = unpackf(short_format, header, offset=154)[0]
    meta["curve_offset"] = unpackf(int_format, header, offset=16)[0]
    # scaling factors
    meta["vscale"] = unpackf(double_format, header, offset=168 - v1_offset)[0]
    meta["voffset"] = unpackf(double_format, header, offset=176 - v1_offset)[0]
    # meta['tstart'] = unpackf('d', header, offset=496)[0]
    meta["tstart"] = unpackf(double_format, header, offset=488 - v1_offset)[0]
    meta["tscale"] = unpackf(double_format, header, offset=536 - v1_offset)[0]
    # trigger detail
    meta["tfrac"] = unpackf(double_format, header, offset=788 - v1_offset)[0]
    meta["tdatefrac"] = unpackf(double_format, header, offset=796)[0]
    meta["tdate"] = unpackf(uint_format, header, offset=804 - v1_offset)[0]
    # data offsets
    # frames are same size, only first frame offsets are used
    dsize = unpackf(uint_format, header, offset=818 - v1_offset)[0]
    meta["dsize"] = dsize
    # sample data type detection
    code = unpackf(int_format, header, offset=240 - v1_offset)[0]
    meta["code"] = code
    bps = unpackf(byte_format, header, offset=15)[0]  # bytes-per-sample
    meta["bps"] = bps
    if code == 7 and bps == 1:
        dformat = endianness + "i1"
    elif code == 0 and bps == 2:
        dformat = endianness + "i2"
    elif code == 4 and bps == 4:
        dformat = endianness + "f32"
    else:
        raise WfmReadError(
            path, f"Data type code {code} or bytes-per-sample {bps} is not supported"
        )
    meta["dformat"] = dformat
    meta["dlen"] = dsize // bps
    return meta


class ScopeData(IScopeData):
    """
    Class for WFM oscillogram data from 5 and 6 Series MSO Tek Oscilloscopes
    """

    def __init__(self, path: str) -> None:
        """
        Initialize ScopeData object.

        Parameters
        ----------
        path : str
            Path to WFM file.

        Notes
        -----
        Reads WFM file and populates object with data and metadata.
        If file cannot be read, raises WfmReadError.
        """
        self.y, meta = read_wfm(path)
        for k, v in meta.items():
            setattr(self, k, v)

        samples = len(self.y)
        self.tstop = samples * self.tscale + self.tstart
        self.x = np.linspace(self.tstart, self.tstop, samples, endpoint=False)
        self.horizInterval = self.x[1] - self.x[0]
