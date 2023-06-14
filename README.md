[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/vongostev/TekWFM2.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/vongostev/TekWFM2/context:python)
[![tekwfm2](https://github.com/vongostev/TekWFM2/actions/workflows/python-publish.yml/badge.svg)](https://github.com/vongostev/TekWFM2/actions/workflows/python-publish.yml)
## TekWFM2
Parser for [Tektronix WFM v.1 & v.2 binary files](https://download.tek.com/manual/Waveform-File-Format-Manual-077022011.pdf) based on [the related post](https://forum.tek.com/viewtopic.php?t=141081). 
ScopeData interface is unified with [LeCroyParser](https://github.com/bennomeier/leCroyParser) interface with fields 'x', 'y', 'horizInterval'.

Module reads volts vs. time records (including fastframes) from little- and big-endian version 1 & 2 WFM files


### Note
I have not tested for version 1 and 2 WFM files because I have only version 3 files measured by MSO6 series. 

Added by ykm11

