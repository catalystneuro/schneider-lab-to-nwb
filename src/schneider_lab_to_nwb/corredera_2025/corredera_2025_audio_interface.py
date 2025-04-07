"""Primary class for converting audio recordings."""
from pynwb.file import NWBFile
from pydantic import FilePath
import numpy as np
from pymatreader import read_mat
from pynwb.behavior import BehavioralTimeSeries, TimeSeries
from pynwb.device import Device
from ndx_events import Events, AnnotatedEventsTable
import os

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import get_base_schema
from neuroconv.tools import nwb_helpers
from neuroconv.tools.hdmf import SliceableDataChunkIterator


class Corredera2025AudioInterface(BaseDataInterface):
    """Audio interface for corredera_2025 conversion"""

    keywords = ("audio",)

    def __init__(self, file_path: FilePath, verbose: bool = True):
        """Initialize the audio interface.

        Parameters
        ----------
        file_path : FilePath
            Path to the audio .mic file.
        verbose : bool, optional
            Whether to print verbose output, by default True.
        """
        super().__init__(file_path=file_path)
        self.verbose = verbose

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, stub_test: bool = False):
        # Define constants
        NUM_CHANNELS = 4
        SAMPLING_RATE = 192_000.0

        # Read Data
        file_path = self.source_data["file_path"]
        num_channels = 4
        file_size = os.path.getsize(file_path)
        dtype = np.dtype("float32")
        num_samples = int(file_size // (dtype.itemsize * num_channels))
        if stub_test:
            num_samples = min(num_samples, int(SAMPLING_RATE))
        memmaped_data = np.memmap(file_path, dtype=dtype, mode="r", shape=(num_samples, num_channels))
        data = SliceableDataChunkIterator(data=memmaped_data, display_progress=self.verbose)

        # Add Data to NWBFile
        audio_series = TimeSeries(
            name="AudioRecording",
            data=data,
            unit="a.u.",
            rate=SAMPLING_RATE,
            description="Audio recording from four AVISOFT microphones.",
        )
        nwbfile.add_acquisition(audio_series)

        # Add Devices
        for device_kwargs in metadata["Audio"]["Microphones"]:
            device = Device(**device_kwargs)
            nwbfile.add_device(device)
