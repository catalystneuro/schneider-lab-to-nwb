"""Primary class for converting audio recordings."""
from pynwb.file import NWBFile
from pydantic import FilePath
import numpy as np
from pymatreader import read_mat
from pynwb.behavior import BehavioralTimeSeries, TimeSeries
from pynwb.device import Device
from pynwb.core import DynamicTableRegion
from ndx_events import Events, AnnotatedEventsTable
import os
from ndx_sound import (
    Speaker,
    Microphone,
    AcousticRecordingSeries,
    AcousticStimulusSeries,
    MicrophoneTable,
    AcousticLabMetaData,
    AudioInterfaceDevice,
)

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
        # microphone_schema = get_schema_from_hdmf_class(Microphone)
        # microphone_schema["additionalProperties"] = True
        # acoustic_recording_series_schema = get_schema_from_hdmf_class(AcousticRecordingSeries)
        # acoustic_recording_series_schema["required"].remove("unit")
        # acoustic_recording_series_schema["required"].remove("microphones")
        # metadata_schema["properties"]["Audio"] = {
        #     "type": "object",
        #     "properties": {
        #         # "Microphones": {
        #         #     "type": "array",
        #         #     "items": microphone_schema,
        #         #     "description": "List of microphones used for recording.",
        #         # },
        #         "AudioRecording": acoustic_recording_series_schema,
        #         "additionalProperties": True,
        #     },
        # }
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

        # Add Devices
        # for device_kwargs in metadata["Audio"]["Microphones"]:
        #     device = Microphone(**device_kwargs)
        #     nwbfile.add_device(device)
        #     microphones.append(device)
        microphone_kwargs = {
            "name": "Microphone",
            "description": "Microphone used for recording.",
            "frequency_range_in_hz": [20.0, 20_000.0],
            "sensitivity_in_mv_per_pa": 1.0,
        }
        microphone = Microphone(**microphone_kwargs)
        nwbfile.add_device(microphone)
        audio_interface_device = AudioInterfaceDevice(
            name="AudioInterface",
            description="Audio interface used for recording.",
            signal_to_noise_ratio_in_db=115.0,
            channel_separation_in_db=110.0,
        )
        nwbfile.add_device(audio_interface_device)

        microphone_table = MicrophoneTable(
            name="MicrophoneTable",
            description="Table of microphones used for recording.",
        )
        for i in range(4):
            microphone_table.add_row(
                microphone=microphone,
                audio_interface_device=audio_interface_device,
                location=f"Location {i+1}",
            )
        microphone_table_region = microphone_table.create_microphone_table_region(
            description="Region of microphones used for recording.",
            region=[0, 1, 2, 3],
        )

        acoustic_lab_meta_data = AcousticLabMetaData(
            name="AcousticLabMetaData",
            microphone_table=microphone_table,
        )
        nwbfile.add_lab_meta_data(acoustic_lab_meta_data)

        # Add Data to NWBFile
        # audio_kwargs = metadata["Audio"]["AudioRecording"]
        audio_kwargs = {"name": "AcousticRecordingSeries", "description": "my description"}
        audio_kwargs["data"] = data
        audio_kwargs["rate"] = SAMPLING_RATE
        audio_kwargs["unit"] = "a.u."
        audio_kwargs["microphone_table_region"] = microphone_table_region
        audio_series = AcousticRecordingSeries(**audio_kwargs)
        nwbfile.add_acquisition(audio_series)
