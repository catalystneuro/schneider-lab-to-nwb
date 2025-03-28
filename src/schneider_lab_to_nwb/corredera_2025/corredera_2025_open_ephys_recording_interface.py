"""Primary class for converting OpenEphys Recordings."""
from pynwb.file import NWBFile
import numpy as np
from typing import Literal

from neuroconv.datainterfaces import OpenEphysBinaryRecordingInterface
from spikeinterface.extractors import OpenEphysBinaryRecordingExtractor


class Corredera2025OpenEphysRecordingInterface(OpenEphysBinaryRecordingInterface):
    """OpenEphys RecordingInterface for corredera_2025 conversion."""

    Extractor = OpenEphysBinaryRecordingExtractor

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata["Ecephys"]["Device"] = []  # remove default device
        return metadata

    def add_to_nwbfile(
        self, nwbfile: NWBFile, metadata: dict, brain_region: Literal["A1", "M2"] = "A1", **conversion_options
    ):
        """Add the recording to an NWBFile.

        Parameters
        ----------
        nwbfile : pynwb.NWBFile
            The in-memory object to add the data to.
        metadata : dict
            Metadata dictionary with information used to create the NWBFile.
        brain_region : Literal["A1", "M2"], optional
            The brain region from which the recording was taken, by default "A1".
        """
        # folder_path = self.source_data["folder_path"]
        # channel_positions = np.load(folder_path / "channel_positions.npy")
        # location = metadata["BrainRegion"][brain_region]["electrode_group_location"]
        # for electrode_group in metadata["Ecephys"]["ElectrodeGroup"]:
        #     electrode_group["location"] = location
        # channel_ids = self.recording_extractor.get_channel_ids()
        # self.recording_extractor.set_channel_locations(channel_ids=channel_ids, locations=channel_positions)
        # self.recording_extractor.set_property(key="brain_area", ids=channel_ids, values=[location] * len(channel_ids))
        # self.recording_extractor._recording_segments[0].t_start = 0.0

        super().add_to_nwbfile(nwbfile=nwbfile, metadata=metadata, **conversion_options)
