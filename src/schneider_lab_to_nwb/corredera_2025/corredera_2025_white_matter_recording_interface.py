"""Primary class for converting WhiteMatter Recordings."""
from pynwb.file import NWBFile
import numpy as np
from typing import Literal

from neuroconv.datainterfaces import WhiteMatterRecordingInterface
from spikeinterface.extractors import WhiteMatterRecordingExtractor
from probeinterface import get_probe


class Corredera2025WhiteMatterRecordingInterface(WhiteMatterRecordingInterface):
    """WhiteMatter RecordingInterface for corredera_2025 conversion."""

    Extractor = WhiteMatterRecordingExtractor

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata["Ecephys"]["Device"] = []  # remove default device
        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, **conversion_options):
        """Add the recording to an NWBFile.

        Parameters
        ----------
        nwbfile : pynwb.NWBFile
            The in-memory object to add the data to.
        metadata : dict
            Metadata dictionary with information used to create the NWBFile.
        """
        location = "Left auditory cortex"
        num_channels = self.source_data["num_channels"]

        probe = get_probe("cambridgeneurotech", "ASSY-236-P-1")
        probe.set_device_channel_indices(np.arange(num_channels))
        self.recording_extractor = self.recording_extractor.set_probe(probe, group_mode="by_shank")

        channel_ids = self.recording_extractor.get_channel_ids()
        self.recording_extractor.set_property(key="brain_area", ids=channel_ids, values=[location] * len(channel_ids))

        super().add_to_nwbfile(nwbfile=nwbfile, metadata=metadata, **conversion_options)
