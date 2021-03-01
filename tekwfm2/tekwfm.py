# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 15:34:22 2021

@author: Pavel Gostev

WFM v.2 reader
https://www.tek.com/sample-license
reads volts vs. time records (including fastframes) from little-endian version 2 WFM files

See Also
Performance Oscilloscope Reference Waveform File Format
https://download.tek.com/manual/Waveform-File-Format-Manual-077022011.pdf

Based on
https://forum.tek.com/viewtopic.php?t=141081

Tested on Python 3.6+

"""



import struct
import numpy as np


class WfmReadError(Exception):
    """error for unexpected things"""
    pass


def read_wfm(target):
    """return sample data from target WFM file"""
    with open(target, 'rb') as f:
        hbytes = f.read(838)
        meta = decode_header(hbytes)
        # file signature checks
        if meta['byte_order'] != 0x0f0f:
            raise WfmReadError('big-endian not supported in this version')
        if meta['version'] != b':WFM#002':
            raise WfmReadError('only version 2 wfms supported in this version')
        if meta['imp_dim_count'] != 1:
            raise WfmReadError('imp dim count not 1')
        if meta['exp_dim_count'] != 1:
            raise WfmReadError('exp dim count not 1')
        if meta['record_type'] != 2:
            raise WfmReadError('not WFMDATA_VECTOR')
        # if meta['exp_dim_1_type'] != 0:
        #    raise WfmReadError('not EXPLICIT_SAMPLE')
        if meta['time_base_1'] != 0:
            raise WfmReadError('not BASE_TIME')
        if meta['fastframe']:
            raise WfmReadError('Fast Frames are not supported')
        # read curve block
        bin_wave = np.memmap(filename=f,
                             dtype=meta['dformat'],
                             mode='r',
                             offset=meta['curve_offset'],
                             shape=(meta['dlen']),
                             order='F')

    scaled_array = bin_wave * meta['vscale'] + meta['voffset']
    return scaled_array, meta


def decode_header(header_bytes):
    """returns a dict of wfm metadata"""
    wfm_info = {}
    if len(header_bytes) != 838:
        raise WfmReadError('wfm header bytes not 838')
    wfm_info['byte_order'] = struct.unpack_from('H', header_bytes, offset=0)[0]
    wfm_info['version'] = struct.unpack_from('8s', header_bytes, offset=2)[0]
    wfm_info['imp_dim_count'] = struct.unpack_from(
        'I', header_bytes, offset=114)[0]
    wfm_info['exp_dim_count'] = struct.unpack_from(
        'I', header_bytes, offset=118)[0]
    wfm_info['record_type'] = struct.unpack_from(
        'I', header_bytes, offset=122)[0]
    wfm_info['exp_dim_1_type'] = struct.unpack_from(
        'I', header_bytes, offset=244)[0]
    wfm_info['time_base_1'] = struct.unpack_from(
        'I', header_bytes, offset=768)[0]
    wfm_info['fastframe'] = struct.unpack_from('I', header_bytes, offset=78)[0]
    wfm_info['Frames'] = struct.unpack_from(
        'I', header_bytes, offset=72)[0] + 1
    wfm_info['summary_frame'] = struct.unpack_from(
        'h', header_bytes, offset=154)[0]
    wfm_info['curve_offset'] = struct.unpack_from('i', header_bytes, offset=16)[
        0]  # 838 + ((frames - 1) * 54)
    # scaling factors
    wfm_info['vscale'] = struct.unpack_from('d', header_bytes, offset=168)[0]
    wfm_info['voffset'] = struct.unpack_from('d', header_bytes, offset=176)[0]
    #wfm_info['tstart'] = struct.unpack_from('d', header_bytes, offset=496)[0]
    wfm_info['tstart'] = struct.unpack_from('d', header_bytes, offset=488)[0]
    wfm_info['tscale'] = struct.unpack_from('d', header_bytes, offset=536)[0]
    # trigger detail
    wfm_info['tfrac'] = struct.unpack_from('d', header_bytes, offset=788)[
        0]  # frame index 0
    wfm_info['tdatefrac'] = struct.unpack_from(
        'd', header_bytes, offset=796)[0]  # frame index 0
    wfm_info['tdate'] = struct.unpack_from('I', header_bytes, offset=804)[
        0]  # frame index 0

    # data offsets
    # frames are same size, only first frame offsets are used
    dsize = struct.unpack_from('I', header_bytes, offset=818)[0]
    wfm_info['dsize'] = dsize
    # sample data type detection
    code = struct.unpack_from('i', header_bytes, offset=240)[0]
    wfm_info['code'] = code
    bps = struct.unpack_from('b', header_bytes, offset=15)[
        0]  # bytes-per-sample
    wfm_info['bps'] = bps
    if code == 7 and bps == 1:
        dformat = 'int8'
    elif code == 0 and bps == 2:
        dformat = 'int16'
    elif code == 4 and bps == 4:
        dformat = 'single'
    else:
        raise WfmReadError('data type code or bytes-per-sample not understood')
    wfm_info['dformat'] = dformat
    wfm_info['dlen'] = dsize // bps
    return wfm_info


class ScopeData:

    def __init__(self, path):
        """
        Class for WFM oscillogram data from old Tek Oscilloscopes
        5 Series MSO
        6 Series MSO

        Parameters
        ----------
        path : str
            Full or relative path to oscillogram WFM file.

        """
        try:
            self.y, meta = read_wfm(path)
        except Exception as E:
            raise WfmReadError(path, E)
        
        for k, v in meta.items():
            setattr(self, k, v)
            
        samples = len(self.y)
        self.tstop = samples * self.tscale + self.tstart
        self.x = np.linspace(self.tstart, self.tstop, samples, endpoint=False)
        self.horizInterval = self.x[1] - self.x[0]
