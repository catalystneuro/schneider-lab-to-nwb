"""Primary class for converting experiment-specific behavior."""
import warnings

import numpy as np
from neuroconv import BaseDataInterface
from neuroconv.tools import nwb_helpers
from pydantic import FilePath
from pymatreader import read_mat
from pynwb import NWBFile, TimeSeries
from pynwb.behavior import BehavioralTimeSeries


class LaChioma2024BehaviorInterface(BaseDataInterface):
    """Behavior interface for la_chioma_2024 conversion"""

    keywords = ("behavior",)

    def __init__(self, file_path: FilePath):
        """Initialize the behavior interface.

        Parameters
        ----------
        file_path : FilePath
            Path to the behavior .mat file.
        """
        super().__init__(file_path=file_path)

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, verbose: bool = False):
        """Add behavior data to the NWBFile.

        Parameters
        ----------
        nwbfile : pynwb.NWBFile
            The in-memory object to add the data to.
        metadata : dict
            Metadata dictionary with information used to create the NWBFile.
        verbose: bool, optional
            Whether to print extra information during the conversion, by default False.
        """
        # Read Data
        file_path = self.source_data["file_path"]
        file = read_mat(file_path)

        if "continuous" not in file:
            raise ValueError(f"Expected 'continuous' key in the file, but found: {file.keys()}")
        continuous_data = file["continuous"]
        if "wheel" in continuous_data:
            wheel_data = continuous_data["wheel"]
            # Add wheel data to nwbfile
            behavioral_time_series = []
            aligned_timestamps = wheel_data["time"]  # time vector in "ephys" clock.
            for name, time_series_metadata in metadata["Behavior"]["TimeSeries"].items():
                if name not in wheel_data:
                    warnings.warn(f"Time series '{name}' not found in wheel data.")
                    continue
                data = np.array(wheel_data[name]).squeeze()
                time_series = TimeSeries(
                    name=time_series_metadata["name"],
                    timestamps=aligned_timestamps,
                    data=data,
                    unit=time_series_metadata["unit"],
                    description=time_series_metadata["description"],
                )
                behavioral_time_series.append(time_series)
            # Add Data to NWBFile
            behavior_module = nwb_helpers.get_module(
                nwbfile=nwbfile,
                name=metadata["Behavior"]["Module"]["name"],
                description=metadata["Behavior"]["Module"]["description"],
            )

            # Add BehavioralTimeSeries
            behavioral_time_series = BehavioralTimeSeries(
                time_series=behavioral_time_series,
                name="behavioral_time_series",
            )
            behavior_module.add(behavioral_time_series)
