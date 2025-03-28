"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    PhySortingInterface,
    ExternalVideoInterface,
)

from schneider_lab_to_nwb.corredera_2025 import (
    Corredera2025OpenEphysRecordingInterface,
)


class Corredera2025NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Recording=Corredera2025OpenEphysRecordingInterface,
        Video=ExternalVideoInterface,
    )
