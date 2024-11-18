"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pydantic import FilePath
import numpy as np
from pymatreader import read_mat
from hdmf.common.table import DynamicTableRegion
from pynwb.behavior import BehavioralTimeSeries, TimeSeries
from pynwb.device import Device
from ndx_events import EventTypesTable, EventsTable, Task, TimestampVectorData

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict, get_base_schema
from neuroconv.tools import nwb_helpers


class Schneider2024BehaviorInterface(BaseDataInterface):
    """Behavior interface for schneider_2024 conversion"""

    keywords = ("behavior",)

    def __init__(self, file_path: FilePath):
        super().__init__(file_path=file_path)

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        return metadata

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

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # Read Data
        file_path = self.source_data["file_path"]
        file = read_mat(file_path)
        behavioral_time_series, name_to_times, name_to_values, name_to_trial_array = [], dict(), dict(), dict()
        for time_series_dict in metadata["Behavior"]["TimeSeries"]:
            name = time_series_dict["name"]
            timestamps = np.array(file["continuous"][name]["time"]).squeeze()
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
            name_to_times[name] = times
        for event_dict in metadata["Behavior"]["ValuedEvents"]:
            name = event_dict["name"]
            times = np.array(file["events"][name]["time"]).squeeze()
            values = np.array(file["events"][name]["value"]).squeeze()
            name_to_times[name] = times
            name_to_values[name] = values

        trial_start_times = np.array(file["events"]["push"]["time"]).squeeze()
        trial_stop_times = np.array(file["events"]["push"]["time_end"]).squeeze()
        trial_is_nan = np.isnan(trial_start_times) | np.isnan(trial_stop_times)
        trial_start_times = trial_start_times[np.logical_not(trial_is_nan)]
        trial_stop_times = trial_stop_times[np.logical_not(trial_is_nan)]
        for trials_dict in metadata["Behavior"]["Trials"]:
            name = trials_dict["name"]
            trial_array = np.array(file["events"]["push"][name]).squeeze()
            name_to_trial_array[name] = trial_array[np.logical_not(trial_is_nan)]

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
        event_types_table = EventTypesTable(name="event_types", description="Metadata about event types.")
        event_type_name_to_row = dict()
        i = 0
        for event_dict in metadata["Behavior"]["Events"]:
            event_type_name_to_row[event_dict["name"]] = i
            event_types_table.add_row(
                event_name=event_dict["name"],
                event_type_description=event_dict["description"],
            )
            i += 1
        for event_dict in metadata["Behavior"]["ValuedEvents"]:
            event_type_name_to_row[event_dict["name"]] = i
            event_types_table.add_row(
                event_name=event_dict["name"],
                event_type_description=event_dict["description"],
            )
            i += 1
        events_table = EventsTable(
            name="events_table",
            description="Metadata about events.",
            target_tables={"event_type": event_types_table},
        )
        for event_dict in metadata["Behavior"]["Events"]:
            event_times = name_to_times[event_dict["name"]]
            event_type = event_type_name_to_row[event_dict["name"]]
            for event_time in event_times:
                events_table.add_row(timestamp=event_time, event_type=event_type)
        valued_events_table = EventsTable(
            name="valued_events_table",
            description="Metadata about valued events.",
            target_tables={"event_type": event_types_table},
        )
        valued_events_table.add_column(name="value", description="Value of the event.")
        for event_dict in metadata["Behavior"]["ValuedEvents"]:
            event_times = name_to_times[event_dict["name"]]
            event_values = name_to_values[event_dict["name"]]
            event_type = event_type_name_to_row[event_dict["name"]]
            for event_time, event_value in zip(event_times, event_values):
                valued_events_table.add_row(timestamp=event_time, event_type=event_type, value=event_value)
        behavior_module.add(events_table)
        behavior_module.add(valued_events_table)

        task = Task(event_types=event_types_table)
        nwbfile.add_lab_meta_data(task)

        # Add Trials Table
        for start_time, stop_time in zip(trial_start_times, trial_stop_times):
            nwbfile.add_trial(start_time=start_time, stop_time=stop_time)
        for trials_dict in metadata["Behavior"]["Trials"]:
            name = trials_dict["name"]
            trial_array = name_to_trial_array[name]
            nwbfile.add_trial_column(name=name, description=trials_dict["description"], data=trial_array)

        # Add Epochs Table
        nwbfile.add_epoch(start_time=trial_start_times[0], stop_time=trial_stop_times[-1], tags=["Active Behavior"])
        nwbfile.add_epoch(
            start_time=valued_events_table["timestamp"][0],
            stop_time=valued_events_table["timestamp"][-1],
            tags=["Passive Listening"],
        )

        # Add Devices
        for device_kwargs in metadata["Behavior"]["Devices"]:
            device = Device(**device_kwargs)
            nwbfile.add_device(device)
