"""Primary class for converting SpikeGadgets Ephys Recordings."""
from pynwb.file import NWBFile
from pathlib import Path
from xml.etree import ElementTree
from pydantic import FilePath
import copy
from collections import Counter
import numpy as np

from neuroconv.datainterfaces import OpenEphysLegacyRecordingInterface
from neuroconv.utils import DeepDict
from spikeinterface.extractors import OpenEphysLegacyRecordingExtractor


class Zempolich2024OpenEphysRecordingInterface(OpenEphysLegacyRecordingInterface):
    """OpenEphys RecordingInterface for zempolich_2024 conversion."""

    Extractor = OpenEphysLegacyRecordingExtractor

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata["Ecephys"]["Device"] = []  # remove default device
        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, **conversion_options):
        folder_path = self.source_data["folder_path"]
        channel_positions = np.load(folder_path / "channel_positions.npy")
        if True:  # TODO: Replace with `if stub_test:` once all channels are present in the data
            channel_positions = channel_positions[:1, :]
        location = metadata["Ecephys"]["ElectrodeGroup"][0]["location"]
        channel_ids = self.recording_extractor.get_channel_ids()
        self.recording_extractor.set_channel_locations(channel_ids=channel_ids, locations=channel_positions)
        self.recording_extractor.set_property(key="brain_area", ids=channel_ids, values=[location] * len(channel_ids))
        self.recording_extractor._recording_segments[0].t_start = 0.0

        super().add_to_nwbfile(nwbfile=nwbfile, metadata=metadata, **conversion_options)
