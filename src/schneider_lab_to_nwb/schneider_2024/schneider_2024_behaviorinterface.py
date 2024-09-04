"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pydantic import FilePath
import numpy as np
from h5py import File
from pynwb.behavior import BehavioralTimeSeries, TimeSeries

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict


class Schneider2024BehaviorInterface(BaseDataInterface):
    """Behavior interface for schneider_2024 conversion"""

    keywords = ["behavior"]

    def __init__(self, file_path: FilePath):
        super().__init__(file_path=file_path)

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        file_path = self.source_data["file_path"]
        with File(file_path, "r") as file:
            encoder_timestamps = np.array(file["continuous"]["encoder"]["time"]).squeeze()
            encoder_values = np.array(file["continuous"]["encoder"]["value"]).squeeze()
            lick_timestamps = np.array(file["continuous"]["lick"]["time"]).squeeze()
            lick_values = np.array(file["continuous"]["lick"]["value"]).squeeze()

            target_times = np.array(file["events"]["target"]["time"]).squeeze()
            target_out_times = np.array(file["events"]["targetOUT"]["time"]).squeeze()
            tone_in_times = np.array(file["events"]["toneIN"]["time"]).squeeze()
            tone_out_times = np.array(file["events"]["toneOUT"]["time"]).squeeze()
            tuning_tone_times = np.array(file["events"]["tuningTones"]["time"]).squeeze()
            tuning_tone_values = np.array(file["events"]["tuningTones"]["value"]).squeeze()
            valve_times = np.array(file["events"]["valve"]["time"]).squeeze()

        encoder_time_series = TimeSeries(
            name="encoder",
            timestamps=encoder_timestamps,
            data=encoder_values,
            unit="a.u.",
            description="Sampled values for entire duration of experiment for lever pressing/treadmill behavior read from a quadrature encoder.",
        )
        lick_time_series = TimeSeries(
            name="lick",
            timestamps=lick_timestamps,
            data=lick_values,
            unit="a.u.",
            description="Samples values for entire duration of experiment for voltage signal readout from an infrared/capacitive) lickometer sensor.",
        )
        behavioral_time_series = BehavioralTimeSeries(
            time_series=[encoder_time_series, lick_time_series],
            name="behavioral_time_series",
        )
        nwbfile.add_acquisition(behavioral_time_series)
