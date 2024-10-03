"""Primary class for converting optogenetic stimulation."""
from pynwb.file import NWBFile
from pydantic import FilePath
import numpy as np
from pymatreader import read_mat
from pynwb.device import Device
from pynwb.ogen import OptogeneticSeries, OptogeneticStimulusSite

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools.optogenetics import create_optogenetic_stimulation_timeseries
from neuroconv.utils import DeepDict, get_base_schema
from neuroconv.tools import nwb_helpers


class Schneider2024OptogeneticInterface(BaseDataInterface):
    """Optogenetic interface for schneider_2024 conversion"""

    keywords = ["optogenetics"]

    def __init__(self, file_path: FilePath):
        super().__init__(file_path=file_path)

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()

        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
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
        frequency = 1  # TODO: Get opto stim frequency from schneider lab
        power = 0.1  # TODO: confirm power with schneider lab
        pulse_width = 0.1  # TODO: confirm pulse width with schneider lab

        timestamps, data = [0], [0]
        for onset_time, offset_time in zip(onset_times, offset_times):
            duration = offset_time - onset_time
            num_pulses = int(duration * frequency)
            inter_pulse_interval = 1 / frequency
            for i in range(num_pulses):
                pulse_onset_time = onset_time + i * inter_pulse_interval
                timestamps.append(pulse_onset_time)
                data.append(power)
                pulse_offset_time = pulse_onset_time + pulse_width
                timestamps.append(pulse_offset_time)
                data.append(0)
        timestamps, data = np.array(timestamps, dtype=np.float64), np.array(data, dtype=np.float64)

        # Add Data to NWBFile
        # Add Device
        device = Device(**metadata["Optogenetics"]["Device"])
        nwbfile.add_device(device)

        # Add OptogeneticStimulusSite
        site_metadata = metadata["Optogenetics"]["OptogeneticStimulusSite"]
        location = f"Injection location: {site_metadata['injection_location']} \n Stimulation location: {site_metadata['stimulation_location']}"
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
