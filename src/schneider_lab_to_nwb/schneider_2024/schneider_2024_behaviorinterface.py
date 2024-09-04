"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pydantic import FilePath
import numpy as np
from h5py import File
from hdmf.common.table import DynamicTableRegion
from pynwb.behavior import BehavioralTimeSeries, TimeSeries
from ndx_events import EventTypesTable, EventsTable, Task, TimestampVectorData

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from neuroconv.tools import nwb_helpers


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
        # Read Data
        file_path = self.source_data["file_path"]
        with File(file_path, "r") as file:
            behavioral_time_series, name_to_times, name_to_values = [], dict(), dict()
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

        # Add Data to NWBFile
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name="behavior",
            description="Behavioral data from the experiment.",
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
        events_table.add_column(name="value", description="Value of the event.")
        for event_dict in metadata["Behavior"]["Events"]:
            event_times = name_to_times[event_dict["name"]]
            event_type = event_type_name_to_row[event_dict["name"]]
            for event_time in event_times:
                events_table.add_row(timestamp=event_time, event_type=event_type, value="")
        for event_dict in metadata["Behavior"]["ValuedEvents"]:
            event_times = name_to_times[event_dict["name"]]
            event_values = name_to_values[event_dict["name"]]
            event_type = event_type_name_to_row[event_dict["name"]]
            for event_time, event_value in zip(event_times, event_values):
                events_table.add_row(timestamp=event_time, event_type=event_type, value=str(event_value))
        behavior_module.add(events_table)

        task = Task(event_types=event_types_table)
        nwbfile.add_lab_meta_data(task)
