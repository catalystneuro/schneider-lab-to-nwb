"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    PhySortingInterface,
    VideoInterface,
)
from neuroconv.basedatainterface import BaseDataInterface

from schneider_lab_to_nwb.zempolich_2024 import (
    Zempolich2024OpenEphysRecordingInterface,
    Zempolich2024BehaviorInterface,
    Zempolich2024OptogeneticInterface,
    Zempolich2024IntrinsicSignalOpticalImagingInterface,
)


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
