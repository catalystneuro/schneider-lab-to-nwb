"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import OpenEphysBinaryRecordingInterface


class LaChioma2024NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Recording=OpenEphysBinaryRecordingInterface,
    )
