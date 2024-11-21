"""Primary class for converting optogenetic stimulation."""
from pynwb.file import NWBFile
from pydantic import FilePath
from typing import Literal
import numpy as np
from pymatreader import read_mat
from pynwb.device import Device
from pynwb.ogen import OptogeneticSeries, OptogeneticStimulusSite

from neuroconv.basedatainterface import BaseDataInterface


class Zempolich2024OptogeneticInterface(BaseDataInterface):
    """Optogenetic interface for schneider_2024 conversion"""

    keywords = ["optogenetics"]

    def __init__(self, file_path: FilePath):
        """Initialize the OptogeneticInterface.

        Parameters
        ----------
        file_path : FilePath
            Path to the .mat file containing the optogenetic stimulation data.
        """
        super().__init__(file_path=file_path)

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: dict,
        brain_region: Literal["A1", "M2"] = "A1",
        normalize_timestamps: bool = False,
    ):
        """Add optogenetic stimulation data to the NWBFile.

        Parameters
        ----------
        nwbfile : pynwb.NWBFile
            The in-memory object to add the data to.
        metadata : dict
            Metadata dictionary with information used to create the NWBFile.
        brain_region : Literal["A1", "M2"], optional
            Brain region for which the optogenetic stimulation data will be added, by default "A1".
        normalize_timestamps : bool, optional
            Whether to normalize the timestamps to the start of the first behavioral time series, by default False
        """
        # Read Data
        file_path = self.source_data["file_path"]
        file = read_mat(file_path)
        onset_times = file["events"]["push"]["opto_time"]
        is_opto_trial = np.logical_not(np.isnan(onset_times))
        onset_times = onset_times[is_opto_trial]
        offset_times = file["events"]["push"]["opto_time_end"]
        offset_times = offset_times[is_opto_trial]
        assert np.all(
            np.logical_not(np.isnan(offset_times))
        ), "Some of the offset times are nan when onset times are not nan."
        power = metadata["Optogenetics"]["OptogeneticSeries"]["power"]
        starting_timestamp = file["continuous"][metadata["Behavior"]["TimeSeries"][0]["name"]]["time"][0]
        if normalize_timestamps:
            onset_times = onset_times - starting_timestamp
            offset_times = offset_times - starting_timestamp

        timestamps, data = [], []
        for onset_time, offset_time in zip(onset_times, offset_times):
            timestamps.append(onset_time)
            data.append(power)
            timestamps.append(offset_time)
            data.append(0)
        timestamps, data = np.array(timestamps, dtype=np.float64), np.array(data, dtype=np.float64)

        # Add Data to NWBFile
        # Add Device
        device = Device(**metadata["Optogenetics"]["Device"])
        nwbfile.add_device(device)

        # Add OptogeneticStimulusSite
        site_metadata = metadata["Optogenetics"]["OptogeneticStimulusSite"]
        location = metadata["BrainRegion"][brain_region]["optogenetic_stimulus_site_location"]
        ogen_site = OptogeneticStimulusSite(
            name=site_metadata["name"],
            device=device,
            description=site_metadata["description"],
            excitation_lambda=site_metadata["excitation_lambda"],
            location=location,
        )
        nwbfile.add_ogen_site(ogen_site)

        # Add OptogeneticSeries
        series_metadata = metadata["Optogenetics"]["OptogeneticSeries"]
        optogenetic_series = OptogeneticSeries(
            name=series_metadata["name"],
            site=ogen_site,
            description=series_metadata["description"],
            data=data,
            timestamps=timestamps,
        )
        nwbfile.add_stimulus(optogenetic_series)
