"""Primary NWBConverter class for this dataset."""
from pymatreader import read_mat
import numpy as np
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    PhySortingInterface,
    ExternalVideoInterface,
    SLEAPInterface,
    WhiteMatterRecordingInterface,
)

from schneider_lab_to_nwb.corredera_2025 import (
    Corredera2025AudioInterface,
    Corredera2025StimulusInterface,
    Corredera2025WhiteMatterRecordingInterface,
)


class Corredera2025NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Video=ExternalVideoInterface,
        SLEAP=SLEAPInterface,
        Audio=Corredera2025AudioInterface,
        RawRecording=Corredera2025WhiteMatterRecordingInterface,
        ProcessedRecording=Corredera2025WhiteMatterRecordingInterface,
        Sorting=PhySortingInterface,
        Stimulus=Corredera2025StimulusInterface,
    )

    def temporally_align_data_interfaces(self, metadata: dict | None = None, conversion_options: dict | None = None):
        file_path = self.data_interface_objects["Stimulus"].source_data["file_path"]
        mat_file = read_mat(file_path)
        first_timestamp = mat_file["audio_rec"]["MicTimeStamps"][0]

        ephys_starting_time = mat_file["audio_rec"]["ttl_ephys"]["ttl_ephysTimeStamp"] - first_timestamp
        self.data_interface_objects["RawRecording"].set_aligned_starting_time(ephys_starting_time)
        self.data_interface_objects["ProcessedRecording"].set_aligned_starting_time(ephys_starting_time)
        self.data_interface_objects["Sorting"].set_aligned_starting_time(ephys_starting_time)
        cam_timestamps = mat_file["cam"]["camflir"]["TimeStamps_corr"] - first_timestamp
        self.data_interface_objects["Video"].set_aligned_timestamps([cam_timestamps])
        self.data_interface_objects["SLEAP"].set_aligned_timestamps(cam_timestamps)

        ptb_indices = np.cumsum(mat_file["audio_rec"]["MicNrSamples"]) - 1
        audio_indices = np.arange(0, ptb_indices[-1] + 1)
        audio_timestamps = np.interp(
            audio_indices, ptb_indices, mat_file["audio_rec"]["MicTimeStamps"], left=np.nan, right=np.nan
        )
        audio_timestamps = audio_timestamps - first_timestamp
        self.data_interface_objects["Audio"].set_aligned_timestamps(audio_timestamps)

        self.data_interface_objects["Stimulus"].set_aligned_starting_time(first_timestamp)
