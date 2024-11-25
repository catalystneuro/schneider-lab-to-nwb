"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pydantic import FilePath
import numpy as np
from pymatreader import read_mat
from pynwb.behavior import BehavioralTimeSeries, TimeSeries
from pynwb.device import Device
from ndx_events import Events, AnnotatedEventsTable

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import get_base_schema
from neuroconv.tools import nwb_helpers


class Zempolich2024BehaviorInterface(BaseDataInterface):
    """Behavior interface for schneider_2024 conversion"""

    keywords = ("behavior",)

    def __init__(self, file_path: FilePath):
        """Initialize the behavior interface.

        Parameters
        ----------
        file_path : FilePath
            Path to the behavior .mat file.
        """
        super().__init__(file_path=file_path)

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Behavior"] = get_base_schema(tag="Behavior")
        metadata_schema["properties"]["Behavior"]["properties"]["Module"] = {
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
            },
        }
        metadata_schema["properties"]["Behavior"]["properties"]["TimeSeries"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        }
        metadata_schema["properties"]["Behavior"]["properties"]["Events"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        }
        metadata_schema["properties"]["Behavior"]["properties"]["ValuedEvents"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        }
        metadata_schema["properties"]["Behavior"]["properties"]["Devices"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "manufacturer": {"type": "string"},
                },
            },
        }
        metadata_schema["properties"]["Behavior"]["properties"]["Trials"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        }
        return metadata_schema


    def add_to_nwbfile(
        self, nwbfile: NWBFile, metadata: dict, normalize_timestamps: bool = False, verbose: bool = False
    ):
        """Add behavior data to the NWBFile.

        Parameters
        ----------
        nwbfile : pynwb.NWBFile
            The in-memory object to add the data to.
        metadata : dict
            Metadata dictionary with information used to create the NWBFile.
        normalize_timestamps : bool, optional
            Whether to normalize the timestamps to the start of the first behavioral time series, by default False
        verbose: bool, optional
            Whether to print extra information during the conversion, by default False.
        """
        # Read Data
        file_path = self.source_data["file_path"]
        file = read_mat(file_path)
        behavioral_time_series, name_to_times, name_to_values, name_to_trial_array = [], dict(), dict(), dict()
        starting_timestamp = file["continuous"][metadata["Behavior"]["TimeSeries"][0]["name"]]["time"][0]
        for time_series_dict in metadata["Behavior"]["TimeSeries"]:
            name = time_series_dict["name"]
            timestamps = np.array(file["continuous"][name]["time"]).squeeze()
            if normalize_timestamps:
                timestamps = timestamps - starting_timestamp
            data = np.array(file["continuous"][name]["value"]).squeeze()
            time_series = TimeSeries(
                name=name,
                timestamps=timestamps,
                data=data,
                unit="a.u.",
                description=time_series_dict["description"],
            )
            behavioral_time_series.append(time_series)
        for event_dict in metadata["Behavior"]["Events"]:
            name = event_dict["name"]
            times = np.array(file["events"][name]["time"]).squeeze()
            if normalize_timestamps:
                times = times - starting_timestamp
            name_to_times[name] = times
        for event_dict in metadata["Behavior"]["ValuedEvents"]:
            name = event_dict["name"]
            times = np.array(file["events"][name]["time"]).squeeze()
            if normalize_timestamps:
                times = times - starting_timestamp
            values = np.array(file["events"][name]["value"]).squeeze()
            name_to_times[name] = times
            name_to_values[name] = values

        trial_start_times = np.array(file["events"]["push"]["time"]).squeeze()
        trial_stop_times = np.array(file["events"]["push"]["time_end"]).squeeze()
        trial_is_nan = np.isnan(trial_start_times) | np.isnan(trial_stop_times)
        trial_start_times = trial_start_times[~trial_is_nan]
        trial_stop_times = trial_stop_times[~trial_is_nan]
        if normalize_timestamps:
            trial_start_times = trial_start_times - starting_timestamp
            trial_stop_times = trial_stop_times - starting_timestamp
        for trials_dict in metadata["Behavior"]["Trials"]:
            name = trials_dict["name"]
            dtype = trials_dict["dtype"]
            trial_array = np.array(file["events"]["push"][name]).squeeze()
            if dtype == "bool":
                trial_array[np.isnan(trial_array)] = False
            trial_array = np.asarray(trial_array, dtype=dtype)  # Can't cast to dtype right away bc bool(nan) = True
            name_to_trial_array[name] = trial_array[~trial_is_nan]

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

        # Add Events
        for event_dict in metadata["Behavior"]["Events"]:
            event_times = name_to_times[event_dict["name"]]
            if np.all(np.isnan(event_times)):
                if verbose:
                    print(
                        f"An event provided in the metadata ({event_dict['name']}) will be skipped because no times were found."
                    )
                continue  # Skip if all times are NaNs
            event = Events(
                name=event_dict["name"],
                description=event_dict["description"],
                timestamps=event_times,
            )
            behavior_module.add(event)

        valued_events_table = AnnotatedEventsTable(
            name="valued_events_table",
            description="Metadata about valued events.",
        )
        valued_events_table.add_column(name="value", description="Value of the event.", index=True)
        for event_dict in metadata["Behavior"]["ValuedEvents"]:
            event_times = name_to_times[event_dict["name"]]
            if np.all(np.isnan(event_times)):
                if verbose:
                    print(
                        f"An event provided in the metadata ({event_dict['name']}) will be skipped because no times were found."
                    )
                continue  # Skip if all times are NaNs
            event_values = name_to_values[event_dict["name"]]
            valued_events_table.add_event_type(
                label=event_dict["name"],
                event_description=event_dict["description"],
                event_times=event_times,
                value=event_values,
            )
        if len(valued_events_table) > 0:
            behavior_module.add(valued_events_table)

        # Add Trials Table
        for start_time, stop_time in zip(trial_start_times, trial_stop_times):
            nwbfile.add_trial(start_time=start_time, stop_time=stop_time)
        for trials_dict in metadata["Behavior"]["Trials"]:
            name = trials_dict["name"]
            trial_array = name_to_trial_array[name]
            nwbfile.add_trial_column(name=name, description=trials_dict["description"], data=trial_array)

        # Add Epochs Table
        nwbfile.add_epoch(start_time=trial_start_times[0], stop_time=trial_stop_times[-1], tags=["Active Behavior"])
        if len(valued_events_table) > 0:
            tuning_tone_times = valued_events_table[0].event_times[0]
            nwbfile.add_epoch(
                start_time=tuning_tone_times[0],
                stop_time=tuning_tone_times[-1],
                tags=["Passive Listening"],
            )

        # Add Devices
        for device_kwargs in metadata["Behavior"]["Devices"]:
            device = Device(**device_kwargs)
            nwbfile.add_device(device)
