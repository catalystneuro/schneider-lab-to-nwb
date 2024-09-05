"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    OpenEphysRecordingInterface,
    PhySortingInterface,
    VideoInterface,
)
from neuroconv.basedatainterface import BaseDataInterface

from schneider_lab_to_nwb.schneider_2024 import Schneider2024BehaviorInterface


class Schneider2024VideoInterface(VideoInterface):
    def get_metadata(self):
        metadata = BaseDataInterface.get_metadata(self)
        return metadata


class Schneider2024NWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Recording=OpenEphysRecordingInterface,
        Sorting=PhySortingInterface,
        Behavior=Schneider2024BehaviorInterface,
        Video=Schneider2024VideoInterface,
    )
