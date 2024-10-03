"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    OpenEphysRecordingInterface,
    PhySortingInterface,
    VideoInterface,
)
from neuroconv.basedatainterface import BaseDataInterface

from schneider_lab_to_nwb.schneider_2024 import Schneider2024BehaviorInterface, Schneider2024OptogeneticInterface


class Schneider2024NWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Recording=OpenEphysRecordingInterface,
        Sorting=PhySortingInterface,
        Behavior=Schneider2024BehaviorInterface,
        VideoCamera1=VideoInterface,
        VideoCamera2=VideoInterface,
        Optogenetic=Schneider2024OptogeneticInterface,
    )
