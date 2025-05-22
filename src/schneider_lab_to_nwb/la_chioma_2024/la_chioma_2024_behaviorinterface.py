"""Primary class for converting experiment-specific behavior."""
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd
from ndx_events import AnnotatedEventsTable
from neuroconv import BaseDataInterface
from neuroconv.tools import nwb_helpers
from pydantic import FilePath
from pymatreader import read_mat
from pynwb import NWBFile, TimeSeries
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

    def add_epochs(self, nwbfile: NWBFile, metadata: dict):
        """Add epochs to the NWBFile.

        The start and stop times of the epochs are extracted from the 'timeRange' field in the experiment log.

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

        behavior_module = nwb_helpers.get_module(nwbfile=nwbfile, name=metadata["Behavior"]["Module"]["name"])

        nwbfile.add_epoch_column(name="radius_wheel_cm", description="The radius of the wheel in centimeters.")

        for experiment_index, experiment in enumerate(experiment_log):
            # link the continuous data to the epoch (experiment)
            behavioral_time_series_name = f"behavioral_time_series_{experiment_index + 1}"
            behavioral_time_series = behavior_module.get(behavioral_time_series_name).time_series
            timeseries = [timeseries for timeseries in behavioral_time_series.values()]
            nwbfile.add_epoch(
                start_time=experiment["timeRange"][0],
                stop_time=experiment["timeRange"][1],
                tags=[experiment["type"]],
                timeseries=timeseries,
                radius_wheel_cm=experiment["movs"]["radiusWheel_cm"],
            )

    def add_trials(self, nwbfile: NWBFile, metadata: dict):
        """Add trials to the NWBFile.

        The trials are extracted from the experiment log and added to the NWBFile.

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

        nwbfile.add_trial_column(name="virmen_mode_id", description="The identifier of the VR run mode.")

        for experiment_index, experiment in enumerate(experiment_log):
            if "Mode" in experiment:
                time_ranges = experiment["Mode"]["timeRanges"]
                mode_list = experiment["Mode"]["list"]
                if isinstance(mode_list, int):
                    mode_list = [mode_list]
                    time_ranges = [time_ranges]
                for mode_ind, mode in enumerate(mode_list):
                    nwbfile.add_trial(
                        start_time=time_ranges[mode_ind][0],
                        stop_time=time_ranges[mode_ind][1],
                        virmen_mode_id=mode,
                    )

    def add_events(self, nwbfile: NWBFile, metadata: dict):
        processed_data = self.read_data()
        if "events" not in processed_data:
            warnings.warn(f"Expected 'events' key in the file, but found: {processed_data.keys()}")
            return
        sound_events_data = processed_data["events"]["sound"]
        sound_events_data = pd.DataFrame(sound_events_data)

        events_table_metadata = metadata["Behavior"]["AnnotatedEvents"]["Table"]
        sound_events_table = AnnotatedEventsTable(
            name=events_table_metadata["name"],
            description=events_table_metadata["description"],
        )

        columns_metadata = metadata["Behavior"]["AnnotatedEvents"]["columns"]
        for column_metadata in columns_metadata:
            if column_metadata["name"] not in sound_events_data.columns:
                warnings.warn(f"The metadata column '{column_metadata['name']}' is not present in the events data.")
                continue

            sound_events_table.add_column(
                name=column_metadata["standardized_name"],
                description=column_metadata["description"],
                index=True,
            )
            sound_events_data[column_metadata["name"]] = sound_events_data[column_metadata["name"]].astype(
                column_metadata["dtype"]
            )

        for event_id, events_by_id in sound_events_data.groupby("id"):
            # convert "expIdx" column to 0-based indexing - same as nwbfile.epochs.id
            events_by_id.loc[:, "expIdx"] = events_by_id.loc[:, "expIdx"] - 1
            event_times = events_by_id["time"].to_numpy()
            event_types_dict = {
                col["standardized_name"]: events_by_id[col["name"]].to_numpy()
                for col in columns_metadata
                if col["name"] in events_by_id
            }

            sound_events_table.add_event_type(
                label=str(event_id),
                event_description=f"The event times for sound {event_id}.",
                event_times=event_times,
                **event_types_dict,
            )
        behavior_module = nwb_helpers.get_module(nwbfile=nwbfile, name=metadata["Behavior"]["Module"]["name"])

        behavior_module.add(sound_events_table)

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
        # Add epochs (experiments)
        self.add_epochs(nwbfile=nwbfile, metadata=metadata)
        # Add trials (VR and PlayWaves trials)
        self.add_trials(nwbfile=nwbfile, metadata=metadata)
        # Add sound events
        self.add_events(nwbfile=nwbfile, metadata=metadata)
