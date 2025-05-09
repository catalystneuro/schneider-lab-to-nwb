"""Primary class for converting audio recordings."""
from pynwb.file import NWBFile
from pydantic import FilePath
import numpy as np
from pymatreader import read_mat
from pynwb.behavior import BehavioralTimeSeries, TimeSeries
from pynwb.device import Device
from ndx_events import Events, AnnotatedEventsTable
import os
from copy import deepcopy

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import get_base_schema, get_schema_from_hdmf_class
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

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        device_schema = get_schema_from_hdmf_class(Device)
        time_series_schema = get_schema_from_hdmf_class(TimeSeries)
        time_series_schema["required"].remove("unit")
        metadata_schema["properties"]["Audio"] = {
            "type": "object",
            "properties": {
                "Microphones": {
                    "type": "array",
                    "items": device_schema,
                    "description": "List of microphones used for recording.",
                },
                "AudioRecording": time_series_schema,
            },
        }
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, stub_test: bool = False):
        # Define constants
        NUM_CHANNELS = 4
        SAMPLING_RATE = 192_000.0

        # Read Data
        file_path = self.source_data["file_path"]
        file_size = os.path.getsize(file_path)
        dtype = np.dtype("float32")
        num_samples = int(file_size // (dtype.itemsize * NUM_CHANNELS))
        if stub_test:
            num_samples = min(num_samples, int(SAMPLING_RATE))
        memmaped_data = np.memmap(file_path, dtype=dtype, mode="r", shape=(num_samples, NUM_CHANNELS))
        data = SliceableDataChunkIterator(data=memmaped_data, display_progress=self.verbose)

        # Add Data to NWBFile
        metadata_copy = deepcopy(metadata)  # Avoid modifying the original metadata
        audio_kwargs = metadata_copy["Audio"]["AudioRecording"]
        audio_kwargs["data"] = data
        audio_kwargs["rate"] = SAMPLING_RATE
        audio_kwargs["unit"] = "a.u."
        audio_series = TimeSeries(**audio_kwargs)
        nwbfile.add_acquisition(audio_series)

        # Add Devices
        for device_kwargs in metadata["Audio"]["Microphones"]:
            device = Device(**device_kwargs)
            nwbfile.add_device(device)
