"""Primary class for converting experiment-specific behavior."""
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd
from neuroconv import BaseDataInterface
from neuroconv.tools import nwb_helpers
from pydantic import FilePath
from pymatreader import read_mat
from pynwb import NWBFile, TimeSeries
from pynwb.core import DynamicTable, VectorData
from pynwb.behavior import BehavioralTimeSeries
from pynwb.epoch import TimeIntervals


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
        self._file = None
        super().__init__(file_path=file_path)

    def read_data(self):
        """Read the data from the .mat file.

        Returns
        -------
        dict
            The data read from the .mat file.
        """
        if self._file is None:
            self._file = read_mat(self.source_data["file_path"])
        return self._file

    def add_continuous_data(self, nwbfile: NWBFile, metadata: dict):
        """
        Add continuous behavioral data from a MAT file to the NWBFile.

        Parameters
        ----------
        nwbfile : NWBFile
            The NWBFile object to which the processed data will be added.
        metadata : dict
            A dictionary containing the behavioral module description in `metadata["Behavior"]["Module"]` and
            the time series metadata in `metadata["Behavior"]["TimeSeries"]`.

        Raises
        ------
        ValueError
            If the expected keys are not found in the MAT file.
        """

        processed_data = self.read_data()

        if "continuous" not in processed_data:
            raise ValueError(f"Expected 'continuous' key in the file, but found: {processed_data.keys()}")

        continuous_data = processed_data["continuous"]
        if "wheel" not in continuous_data:
            raise ValueError(f"Expected 'wheel' key in the continuous data, but found: {continuous_data.keys()}")

        wheel_data = pd.DataFrame(continuous_data["wheel"])
        # Add continuous data to nwbfile
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name=metadata["Behavior"]["Module"]["name"],
            description=metadata["Behavior"]["Module"]["description"],
        )
        # Add per experiment id
        behavioral_time_series_dict = defaultdict(list)
        for expIdx, wheel_per_exp_id in wheel_data.groupby("expIdx"):
            ephys_aligned_timestamps = wheel_per_exp_id["time"].to_numpy()  # time vector in "ephys" clock.
            for time_series_metadata in metadata["Behavior"]["TimeSeries"]:
                if time_series_metadata["name"] not in wheel_data:
                    warnings.warn(f"Time series '{time_series_metadata['name']}' not found in wheel data.")
                    continue
                data = np.array(wheel_per_exp_id[time_series_metadata["name"]]).squeeze()
                time_series_name = time_series_metadata["standardized_name"] + f"_{expIdx}"
                time_series = TimeSeries(
                    name=time_series_name,
                    timestamps=ephys_aligned_timestamps,
                    data=data,
                    unit=time_series_metadata["unit"],
                    description=time_series_metadata["description"],
                )
                behavioral_time_series_dict[f"behavioral_time_series_{expIdx}"].append(time_series)

        # Add BehavioralTimeSeries
        for behavioral_time_series_name, time_series_list in behavioral_time_series_dict.items():
            behavioral_time_series = BehavioralTimeSeries(
                time_series=time_series_list,
                name=behavioral_time_series_name,
            )
            behavior_module.add(behavioral_time_series)

    def add_experiments(self, nwbfile: NWBFile, metadata: dict):
        """Add experiments to the NWBFile.

        The start and stop times of the experiment intervals are extracted from the 'timeRange' field in the experiment log.

        Parameters
        ----------
        nwbfile : pynwb.NWBFile
            The in-memory object to add the data to.
        metadata : dict
            Metadata dictionary with information used to create the NWBFile.
        """
        processed_data = self.read_data()
        experiment_log = processed_data["meta"]["expLog"]
        if isinstance(experiment_log, dict):
            experiment_log = [experiment_log]
        sampling_rate = float(experiment_log[0]["vrOutAudLog"]["sounds"]["soundFS"][0])

        experiment_intervals_metadata = metadata["Behavior"]["TimeIntervals"][0]
        experiment_intervals = TimeIntervals(
            name=experiment_intervals_metadata["name"],
            description=experiment_intervals_metadata["description"],
        )
        experiment_intervals.add_column(name="radius_wheel_cm", description="The radius of the wheel in centimeters.")
        experiment_intervals.add_column(name="experiment_id", description="The identifier of the experiment.")
        experiment_intervals.add_column(name="virmen_mode_id", description="The identifier of the VR run mode.")

        behavior_module = nwb_helpers.get_module(nwbfile=nwbfile, name=metadata["Behavior"]["Module"]["name"])
        sound_events = pd.DataFrame(processed_data["events"]["sound"])
        for experiment_index, experiment in enumerate(experiment_log):
            # link the continuous data to the epoch (experiment)
            behavioral_time_series_name = f"behavioral_time_series_{experiment_index + 1}"
            behavioral_time_series = behavior_module.get(behavioral_time_series_name).time_series
            timeseries = [timeseries for timeseries in behavioral_time_series.values()]
            # PlayWaves experiment without VR mode
            if "Mode" not in experiment:
                experiment_intervals.add_interval(
                    start_time=experiment["timeRange"][0],
                    stop_time=experiment["timeRange"][1],
                    experiment_id=str(experiment_index + 1),
                    timeseries=timeseries,
                    tags=[experiment["type"]],
                    virmen_mode_id=str(np.nan),
                    radius_wheel_cm=experiment["movs"]["radiusWheel_cm"],
                )

                filtered_events = sound_events[sound_events["expIdx"] == experiment_index + 1]
                sound = experiment["sound"]
                tones_data = sound["data"]
                if not isinstance(tones_data, list):
                    tones_data = [tones_data]
                for tone_index, tone_data in enumerate(tones_data):
                    more_filtered_events = filtered_events[filtered_events["id"] == tone_index + 1]
                    audio_name = sound["names"][tone_index].replace(".wav", "")
                    audio_series = TimeSeries(
                        name=audio_name,
                        starting_time=more_filtered_events["time"].iloc[0],
                        rate=sampling_rate,
                        description=f"The audio data generated by PlayWaves.",
                        data=tone_data[
                            :, 0
                        ],  # The first channel is the tone being played, the second is a copy of the first. the third and fourth is the TTL.
                        unit="a.u.",
                    )
                    nwbfile.add_stimulus_template(audio_series)
            # If the experiment has a VR mode, extract the time ranges and modes
            else:
                time_ranges = experiment["Mode"]["timeRanges"]
                mode_list = experiment["Mode"]["list"]
                if isinstance(mode_list, int):
                    mode_list = [mode_list]
                    time_ranges = [time_ranges]
                for mode_ind, mode in enumerate(mode_list):
                    experiment_intervals.add_interval(
                        start_time=time_ranges[mode_ind][0],
                        stop_time=time_ranges[mode_ind][1],
                        experiment_id=str(experiment_index + 1),
                        timeseries=timeseries,
                        tags=[experiment["type"]],
                        virmen_mode_id=str(mode),
                        radius_wheel_cm=experiment["movs"]["radiusWheel_cm"],
                    )

        nwbfile.add_time_intervals(experiment_intervals)

    def add_events(self, nwbfile: NWBFile, metadata: dict):
        processed_data = self.read_data()
        if "events" not in processed_data:
            warnings.warn(f"Expected 'events' key in the file, but found: {processed_data.keys()}")
            return
        sound_events_data = processed_data["events"]["sound"]
        stimulus_names = []
        for experiment in processed_data["meta"]["expLog"]:
            names = experiment["sound"]["names"]
            for name in names:
                name = name.replace(".wav", "")
                if name in stimulus_names:
                    continue
                stimulus_names.append(name)
        sound_events_data = pd.DataFrame(sound_events_data)

        columns_metadata = metadata["Behavior"]["AudioStimulus"]
        df_name_to_nwb_name = dict()
        colnames = ["presentation_time"]
        column_name_to_data = {"presentation_time": sound_events_data["time"].to_numpy()}
        column_name_to_description = {"presentation_time": "Time of stimulus presentation"}
        for column_metadata in columns_metadata:
            if column_metadata["name"] not in sound_events_data.columns:
                warnings.warn(f"The metadata column '{column_metadata['name']}' is not present in the events data.")
                continue

            dtype = column_metadata["dtype"]
            column_data = sound_events_data[column_metadata["name"]].to_numpy().astype(dtype)
            column_name_to_data[column_metadata["standardized_name"]] = column_data
            column_name_to_description[column_metadata["standardized_name"]] = column_metadata["description"]
            colnames.append(column_metadata["standardized_name"])
            df_name_to_nwb_name[column_metadata["name"]] = column_metadata["standardized_name"]
        column_name_to_data["stimulus_name"] = np.array(stimulus_names)[sound_events_data["id"].to_numpy() - 1]
        column_name_to_description["stimulus_name"] = "Name of the stimulus ex. sound01_F2000_L65_D0.1+0.005"
        colnames.append("stimulus_name")

        columns = [
            VectorData(name=colname, description=column_name_to_description[colname], data=column_name_to_data[colname])
            for colname in colnames
        ]
        audio_stimulus_table = DynamicTable(
            name="AudioStimulus",
            description="Table of audio stimulus presentations",
            columns=columns,
            colnames=colnames,
        )

        nwbfile.add_stimulus(audio_stimulus_table)

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
        # Add wheel data
        self.add_continuous_data(nwbfile=nwbfile, metadata=metadata)
        # Add experiments
        self.add_experiments(nwbfile=nwbfile, metadata=metadata)
        # Add sound events
        self.add_events(nwbfile=nwbfile, metadata=metadata)
