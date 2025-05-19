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

        expected_keys = ["meta", "continuous", "events"]
        for key in expected_keys:
            if key not in file:
                raise ValueError(f"Expected '{key}' key in the file, but found: {file.keys()}")

        # Add continuous data
        continuous_data = file["continuous"]
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
            aligned_timestamps = wheel_per_exp_id["time"].to_numpy()  # time vector in "ephys" clock.
            for name, time_series_metadata in metadata["Behavior"]["TimeSeries"].items():
                if name not in wheel_data:
                    warnings.warn(f"Time series '{name}' not found in wheel data.")
                    continue
                data = np.array(wheel_per_exp_id[name]).squeeze()
                name = time_series_metadata["name"] + f"_{expIdx}"
                time_series = TimeSeries(
                    name=name,
                    timestamps=aligned_timestamps,
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

        experiment_log = file["meta"]["expLog"]

        if isinstance(experiment_log, dict):
            experiment_log = [experiment_log]

        nwbfile.add_trial_column(
            name="experiment_id",
            description="The identifier of experiment, referring to the whole behavior/ephys session",
        )
        nwbfile.add_trial_column(
            name="type",
            description="The type of trial for each VR Virmen and PlayWaves run.",
        )
        nwbfile.add_trial_column(
            name="vr_mode_id",
            description="VR Virmen mode.",
        )
        for experiment_index, experiment in enumerate(experiment_log):
            behavioral_time_series_name = f"behavioral_time_series_{experiment_index + 1}"
            trial_kwargs = dict(
                experiment_id=experiment_index + 1,
                type=experiment["type"],
                timeseries=behavioral_time_series_dict.get(
                    behavioral_time_series_name
                ),  # link the continuous data to the trial
            )
            if "Mode" not in experiment:
                # For PlayWaves trials
                nwbfile.add_trial(
                    start_time=experiment["timeRange"][0],
                    stop_time=experiment["timeRange"][1],
                    vr_mode_id=np.nan,
                    **trial_kwargs,
                )
            else:
                time_ranges = experiment["Mode"]["timeRanges"]
                mode_list = experiment["Mode"]["list"]
                if isinstance(mode_list, int):
                    mode_list = [mode_list]
                    time_ranges = [time_ranges]

                for mode_ind, mode in enumerate(mode_list):
                    nwbfile.add_trial(
                        start_time=time_ranges[mode_ind][0],
                        stop_time=time_ranges[mode_ind][1],
                        vr_mode_id=float(mode),
                        **trial_kwargs,
                    )

        events_data = file["events"]
        if "sound" in events_data:
            # Add events data to nwbfile
            sound_events_data = pd.DataFrame(events_data["sound"])
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
                    name=column_metadata["name"],
                    description=column_metadata["description"],
                    index=True,
                )
                sound_events_data[column_metadata["name"]] = sound_events_data[column_metadata["name"]].astype(
                    column_metadata["dtype"]
                )

            for event_id, events_by_id in sound_events_data.groupby("id"):
                event_times = events_by_id["time"].to_numpy()
                event_types_dict = {
                    col["name"]: events_by_id[col["name"]].to_numpy()
                    for col in columns_metadata
                    if col["name"] in events_by_id
                }

                sound_events_table.add_event_type(
                    label=str(event_id),
                    event_description=f"The event times for sound {event_id}.",
                    event_times=event_times,
                    **event_types_dict,
                )
            behavior_module.add(sound_events_table)
