from typing import Literal, Protocol, TypedDict

from numpy import float32, int8, int16
from numpy.typing import NDArray


class WfmMeta(TypedDict, total=False):
    byte_order: int
    version: bytes
    imp_dim_count: int
    exp_dim_count: int
    record_type: int
    exp_dim_1_type: int
    time_base_1: int
    fastframe: int
    Frames: int
    summary_frame: int
    curve_offset: int
    vscale: float
    voffset: float
    tstart: float
    tscale: float
    tfrac: float
    tdatefrac: float
    tdate: int
    dsize: int
    code: int
    dformat: str
    dlen: int
    bps: int


class IScopeData(Protocol):
    byte_order: int
    version: bytes
    imp_dim_count: int
    exp_dim_count: int
    record_type: int
    exp_dim_1_type: int
    time_base_1: int
    fastframe: int
    Frames: int
    summary_frame: int
    curve_offset: int
    vscale: float
    voffset: float
    tstart: float
    tscale: float
    tstop: float
    tfrac: float
    tdatefrac: float
    tdate: int
    dsize: int
    code: int
    dformat: Literal["<i1", ">i1", "<i2", ">i2", "<f32", ">f32"]
    dlen: int
    bps: int
    y: NDArray[int8] | NDArray[int16] | NDArray[float32]
    x: NDArray[float32]
    horizInterval: float
