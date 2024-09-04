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
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name="behavior",
            description="Behavioral data from the experiment.",
        )
        behavior_module.add(behavioral_time_series)

        event_types_table = EventTypesTable(name="event_types", description="Metadata about event types.")
        event_types_table.add_row(
            event_name="target", event_type_description="Time at which the target zone is entered during a press."
        )
        event_types_table.add_row(
            event_name="target_out", event_type_description="Time at which the target zone is overshot during a press."
        )
        event_types_table.add_row(
            event_name="tone_in", event_type_description="Time at which target entry tone is played."
        )
        event_types_table.add_row(
            event_name="tone_out", event_type_description="Time at which target exit tone is played."
        )
        event_types_table.add_row(
            event_name="tuning_tone",
            event_type_description="Times at which tuning tones are played to an animal after a behavioral experiment during ephys recording sessions.",
        )
        event_types_table.add_row(
            event_name="valve",
            event_type_description="Times at which solenoid valve opens to deliver water after a correct trial.",
        )

        events_table = EventsTable(
            name="events_table",
            description="Metadata about events.",
            target_tables={"event_type": event_types_table},
        )
        nested_event_times = [
            target_times,
            target_out_times,
            tone_in_times,
            tone_out_times,
            tuning_tone_times,
            valve_times,
        ]
        for i, event_times in enumerate(nested_event_times):
            for event_time in event_times:
                events_table.add_row(timestamp=event_time, event_type=i)
        behavior_module.add(events_table)

        task = Task(event_types=event_types_table)
        nwbfile.add_lab_meta_data(task)
