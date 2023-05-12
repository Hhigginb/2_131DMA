"""
Analog I/O Function
    Serge Lafontaine
    Revisions:
    - 20221116: Disabled one exception and return of missing and bad samples
    - 20221116: Added power function, close statement.
Derived from:
    DWF Python Example
    Author:  Digilent, Inc.
    Revision:  2019-07-23
Description:
    x, y = adda(u, rate=100000, output_range = 0., input_range_1 = 2.0, input_range_2 = 0.0)
    where:
    u: numpy array for the analog signal to be displayed to output channel 0
    rate: sampling frequency for input and output channels
    output_range: maximum absolute value of the output signal. If unspecified set to maximum value of u.
    input_range_1: Either 2 or 50 for the Digilent Pro. It is coerced to the device supported value that is equal or larger.
    input_range_2: Either 2 or 50 for the Digilent Pro. It is coerced to the device supported value that is equal or larger.
    x: numpy array from channel 0
    y: numpy array from channel 1
Requirements:
    The Digilent file "dwfconstants.py" must be in the path.
"""
from dwfconstants import *
import ctypes
import sys
import wave
import numpy as np
import matplotlib.pyplot as plt


class discovery:
    def __init__(self):
        if sys.platform.startswith("win"):
            dwf = cdll.dwf
        elif sys.platform.startswith("darwin"):
            dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
        else:
            dwf = cdll.LoadLibrary("libdwf.so")

        hdwf = c_int()
        dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

        if hdwf.value == 0:
            szerr = create_string_buffer(512)
            dwf.FDwfGetLastErrorMsg(szerr)
            raise Exception("Failed to open device, return code: " + str(szerr.value))
        # Set output power to zero and enable.
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(0), c_int(0), c_double(True))
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(0), c_int(1), c_double(0.))
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(1), c_int(0), c_double(True))
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(1), c_int(1), c_double(0.))
        dwf.FDwfAnalogIOEnableSet(hdwf, c_int(True))
        self.dwf = dwf
        self.hdwf = hdwf
        self.input_range_1 = 0.
        self.input_range_2 = 0.
        self.output_range = 0.
    def close(self):
        # master disable
        dwf = self.dwf
        hdwf = self.hdwf
        # Disable power supply
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(0), c_int(1), c_double(0.))
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(1), c_int(1), c_double(0.))
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(0), c_int(0), c_double(False))
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(1), c_int(0), c_double(False))
        dwf.FDwfAnalogIOEnableSet(hdwf, c_int(False))
        dwf.FDwfDeviceClose(hdwf)
    """
    Description:
        power(vplus=None, vminus=None)
        where:
        vplus: voltage to apply to positive supply
        vminus: voltage to apply to negative supply
        only the absolute value of vplus or vminus is significant.
    """
    def power(self, vplus=None, vminus=None):
        # set up analog IO channel nodes
        # enable positive supply
        dwf = self.dwf
        hdwf = self.hdwf
        # set positive voltage
        if vplus:
            dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(0), c_int(1), c_double(abs(vplus)))
        # set negative voltage
        if vminus:
            # enable negative supply
            dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(1), c_int(1), c_double(-abs(vminus)))

    """
    Description:
        x, y = addas(u, rate=100000, vplus=None, vminus=None, output_range = 0., input_range = 2.0)
        where:
        u: numpy array for the analog signal to be displayed to output channel 0
        rate: sampling frequency for input and output channels
        vplus: positive voltage to output on power supply V+
        vminus: negative voltage to output on power supply V-
        output_range: maximum absolute value of the output signal. If unspecified set to maximum value of u.
        input_range: Either 2 or 50 for the Digilent Pro. It is coerced to the device supported value that is equal or larger.
        x: numpy array from channel 0
        y: numpy array from channel 1
    """
    def adda(self, u, rate=100000, output_range = 0.0, input_range_1 = 0.0, input_range_2 = 0,):

        length = u.size

        # Check input and output ranges
        if output_range == 0. :
            output_range = np.max(np.abs(u))
        if input_range_1 == 0. :
            input_range_1 = output_range
        if input_range_2 == 0. :
            input_range_2 = output_range


        sRun = 1.0 * length / rate

        iRecord = 0
        record0 = (c_int16 * length)()
        record1 = (c_int16 * length)()
        # set up acquisition
        dwf = self.dwf
        hdwf = self.hdwf
        dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_int(1))  # channel 1
        dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(1), c_int(1))  # channel 2
        dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(-1), c_double(input_range_1)) # set default range
        dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(input_range_1))
        dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(1), c_double(input_range_2))
        dwf.FDwfAnalogInChannelOffsetSet(hdwf, c_int(-1), c_double(0))
        dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeRecord)
        dwf.FDwfAnalogInFrequencySet(hdwf, c_double(rate))
        dwf.FDwfAnalogInRecordLengthSet(hdwf, c_double(sRun))
        dwf.FDwfAnalogInTriggerPositionSet(hdwf, c_double(0))
        dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcAnalogOut1)
        dwf.FDwfAnalogInConfigure(hdwf, c_int(0), c_int(1))

        # Get exact input ranges
        exact_input_range_1 = c_double(0.)
        exact_input_range_2 = c_double(0.)
        dwf.FDwfAnalogInChannelRangeGet(hdwf, c_int(0), byref(exact_input_range_1))
        dwf.FDwfAnalogInChannelRangeGet(hdwf, c_int(1), byref(exact_input_range_2))

        iPlay = 0
        channel = c_int(0)  # AWG 1
        dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, 0, c_int(1))
        dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, 0, funcPlay)
        dwf.FDwfAnalogOutRepeatSet(hdwf, channel, c_int(1))

        dwf.FDwfAnalogOutRunSet(hdwf, channel, c_double(sRun))
        dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, 0, c_double(rate))
        dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, 0, c_double(output_range))

        exact_output_range = c_double()
        dwf.FDwfAnalogOutNodeAmplitudeGet(hdwf, channel, 0, byref(exact_output_range))

        self.input_range_1 = exact_input_range_1.value
        self.input_range_2 = exact_input_range_2.value
        self.output_range = exact_output_range.value

        # Scale Data to unity range
        data_array = u / exact_output_range.value
        data = (ctypes.c_double * data_array.size)(*data_array)

        # prime the buffer with the first chunk of data
        cBuffer = c_int(0)
        dwf.FDwfAnalogOutNodeDataInfo(hdwf, channel, 0, 0, byref(cBuffer))
        if cBuffer.value > length: cBuffer.value = length
        dwf.FDwfAnalogOutNodeDataSet(hdwf, channel, 0, data, cBuffer)
        iPlay += cBuffer.value
        dwf.FDwfAnalogOutConfigure(hdwf, channel, c_int(1))

        dataLost = c_int(0)
        dataFree = c_int(0)
        dataAvailable = c_int(0)
        dataCorrupted = c_int(0)
        sts = c_ubyte(0)
        totalLost = 0
        totalCorrupted = 0

        # loop to send out and read in data chunks
        while iRecord < length:
            if dwf.FDwfAnalogOutStatus(hdwf, channel, byref(sts)) != 1:  # handle error
                szerr = create_string_buffer(512)
                dwf.FDwfGetLastErrorMsg(szerr)
                dwf.FDwfAnalogOutReset(hdwf, channel)
                raise Exception(szerr.value)

            # play, analog out data chunk
            if sts.value == DwfStateRunning.value and iPlay < length:  # running and more data to stream
                dwf.FDwfAnalogOutNodePlayStatus(hdwf, channel, 0, byref(dataFree), byref(dataLost), byref(dataCorrupted))
                totalLost += dataLost.value
                totalCorrupted += dataCorrupted.value
                if iPlay + dataFree.value > length:  # last chunk might be less than the free buffer size
                    dataFree.value = length - iPlay
                if dataFree.value > 0:
                    if dwf.FDwfAnalogOutNodePlayData(hdwf, channel, 0, byref(data, iPlay * 8),
                                                     dataFree) != 1:  # offset for double is *8 (bytes)
                        dwf.FDwfAnalogOutReset(hdwf, channel)
                        raise Exception ("Error")
                    iPlay += dataFree.value

            if dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts)) != 1:  # handle error
                szerr = create_string_buffer(512)
                dwf.FDwfGetLastErrorMsg(szerr)
                dwf.FDwfAnalogOutReset(hdwf, channel)
                raise Exception(szerr.value)

            # record, analog in data chunk
            if sts.value == DwfStateRunning.value or sts.value == DwfStateDone.value:  # recording or done
                dwf.FDwfAnalogInStatusRecord(hdwf, byref(dataAvailable), byref(dataLost), byref(dataCorrupted))
                iRecord += dataLost.value
                totalLost += dataLost.value
                totalCorrupted += dataCorrupted.value
                if dataAvailable.value > 0:
                    if iRecord + dataAvailable.value > length:
                        dataAvailable = c_int(length - iRecord)
                    dwf.FDwfAnalogInStatusData16(hdwf, c_int(0), byref(record0, 2 * iRecord), c_int(0),
                                                 dataAvailable)  # get channel 1 data chunk, offset for 16bit data is 2*
                    dwf.FDwfAnalogInStatusData16(hdwf, c_int(1), byref(record1, 2 * iRecord), c_int(0),
                                                 dataAvailable)  # get channel 2 data chunk
                    iRecord += dataAvailable.value

        if totalLost != 0 or totalCorrupted != 0 :
            pass # raise Exception ("Bad Data End.")

        try:
            record0 = np.ctypeslib.as_array(record0)
            record1 = np.ctypeslib.as_array(record1)
        except:
            raise Exception (" No Data")

        range0 =  c_double()
        dwf.FDwfAnalogInChannelRangeGet(hdwf, c_int(0), byref(range0))
        offset0 = c_double()
        dwf.FDwfAnalogInChannelOffsetGet(hdwf, c_int(0), byref(offset0))
        scaling_to_volts = range0.value / 65536.
        offset = offset0.value
        record0 = scaling_to_volts * record0 + offset
        range1 =  c_double()
        dwf.FDwfAnalogInChannelRangeGet(hdwf, c_int(1), byref(range1))
        offset1 = c_double()
        dwf.FDwfAnalogInChannelOffsetGet(hdwf, c_int(1), byref(offset1))
        scaling_to_volts = range1.value / 65536.
        offset = offset1.value
        record1 = scaling_to_volts * record1 + offset

        dwf.FDwfAnalogOutReset(hdwf, channel)

        return record0, record1, totalLost, totalCorrupted

    def inquire_ranges(self):
        return self.input_range_1, self.input_range_2, self.output_range


