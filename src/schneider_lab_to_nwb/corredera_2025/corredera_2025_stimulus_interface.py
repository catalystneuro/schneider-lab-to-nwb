"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pydantic import FilePath
import numpy as np
from pymatreader import read_mat
from pynwb.behavior import BehavioralTimeSeries, TimeSeries
from pynwb.device import Device
from pynwb.core import DynamicTable
from ndx_events import Events, AnnotatedEventsTable
from pathlib import PureWindowsPath

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import get_base_schema, get_schema_from_hdmf_class
from neuroconv.tools import nwb_helpers


class Corredera2025StimulusInterface(BaseDataInterface):
    """Stimulus interface for corredera_2025 conversion"""

    keywords = ("auditory stimulus",)

    def __init__(self, file_path: FilePath):
        """Initialize the interface.

        Parameters
        ----------
        file_path : FilePath
            Path to the .mat file.
        """
        super().__init__(file_path=file_path)

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        device_schema = get_schema_from_hdmf_class(Device)
        metadata_schema["properties"]["Stimulus"] = {
            "type": "object",
            "properties": {
                "Speakers": {
                    "type": "array",
                    "items": device_schema,
                    "description": "List of speakers used for audio stimulus.",
                },
            },
        }
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        file_path = self.source_data["file_path"]
        file = read_mat(file_path)
        epoch_names = ["fullBattery", "exploration", "threat"]
        audio_stimulus_table = DynamicTable(
            name="AudioStimulus",
            description="Table of audio stimulus presentations",
        )
        audio_stimulus_table.add_column(
            name="presentation_time",
            description="Time of stimulus presentation",
        )
        audio_stimulus_table.add_column(
            name="stimulus_name",
            description="Name of the stimulus ex. sound01_F2000_L65_D0.1+0.005",
        )
        for epoch_name in epoch_names:
            sound_data = file["sounds"][epoch_name]["soundData"]
            soundTimeStamps = file["sounds"][epoch_name]["soundTimeStamps"]
            rates = file["sounds"][epoch_name]["soundFS"]
            names = [PureWindowsPath(path).stem for path in file["sounds"][epoch_name]["wavFiles_fullpath"]]

            for name, data, rate, presentation_times in zip(names, sound_data, rates, soundTimeStamps):
                rate = float(rate)
                template_time_series = TimeSeries(
                    name=name,
                    data=data,
                    unit="a.u.",
                    rate=rate,
                )
                nwbfile.add_stimulus_template(template_time_series)
                for i, presentation_time in enumerate(presentation_times):
                    audio_stimulus_table.add_row(
                        presentation_time=presentation_time,
                        stimulus_name=name,
                    )
        nwbfile.add_stimulus(audio_stimulus_table)

        for device_kwargs in metadata["Stimulus"]["Speakers"]:
            device = Device(**device_kwargs)
            nwbfile.add_device(device)
