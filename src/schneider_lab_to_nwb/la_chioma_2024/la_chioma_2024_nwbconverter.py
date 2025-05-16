"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import OpenEphysBinaryRecordingInterface

from schneider_lab_to_nwb.la_chioma_2024.la_chioma_2024_behaviorinterface import LaChioma2024BehaviorInterface


class LaChioma2024NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Recording=OpenEphysBinaryRecordingInterface,
        Behavior=LaChioma2024BehaviorInterface,
    )
