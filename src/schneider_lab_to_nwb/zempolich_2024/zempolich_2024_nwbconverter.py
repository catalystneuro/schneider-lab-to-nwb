"""Primary NWBConverter class for this dataset."""
from pathlib import Path
from pymatreader import read_mat
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    PhySortingInterface,
    VideoInterface,
)

from schneider_lab_to_nwb.zempolich_2024 import (
    Zempolich2024OpenEphysRecordingInterface,
    Zempolich2024BehaviorInterface,
    Zempolich2024OptogeneticInterface,
    Zempolich2024IntrinsicSignalOpticalImagingInterface,
)
from schneider_lab_to_nwb.zempolich_2024.zempolich_2024_behaviorinterface import get_starting_timestamp


class Zempolich2024NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Recording=Zempolich2024OpenEphysRecordingInterface,
        Sorting=PhySortingInterface,
        Behavior=Zempolich2024BehaviorInterface,
        VideoCamera1=VideoInterface,
        VideoCamera2=VideoInterface,
        Optogenetic=Zempolich2024OptogeneticInterface,
        ISOI=Zempolich2024IntrinsicSignalOpticalImagingInterface,
    )

    def temporally_align_data_interfaces(self) -> None:
        """Align timestamps between data interfaces.

        It is called by run_conversion() after the data interfaces have been initialized but before the data is added
        to the NWB file.
        In its current implementation, this method aligns timestamps between the behavior and video data interfaces.
        """
        behavior_interface = self.data_interface_objects["Behavior"]
        behavior_file_path = Path(behavior_interface.source_data["file_path"])
        file = read_mat(behavior_file_path)
        cam1_timestamps, cam2_timestamps = file["continuous"]["cam"]["time"]
        if self.conversion_options["Behavior"].get("normalize_timestamps", False):
            starting_timestamp = get_starting_timestamp(mat_file=file)
            cam1_timestamps -= starting_timestamp
            cam2_timestamps -= starting_timestamp
        self.data_interface_objects["VideoCamera1"].set_aligned_timestamps([cam1_timestamps])
        self.data_interface_objects["VideoCamera2"].set_aligned_timestamps([cam2_timestamps])

    # NOTE: passing in conversion_options as an attribute is a temporary solution until the neuroconv library is updated
    #  to allow for easier customization of the conversion process
    # (see https://github.com/catalystneuro/neuroconv/pull/1162).
    def run_conversion(self, **kwargs):
        self.conversion_options = kwargs["conversion_options"]
        super().run_conversion(**kwargs)
