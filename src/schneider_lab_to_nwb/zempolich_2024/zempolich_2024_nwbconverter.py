"""Primary NWBConverter class for this dataset."""
from pathlib import Path
from pymatreader import read_mat
from typing import Optional
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

# neuroconv.NWBConverter.run_conversion imports
import warnings
from pathlib import Path
from typing import Literal, Optional
from pydantic import FilePath
from pynwb import NWBFile
from neuroconv.tools.nwb_helpers._metadata_and_file_helpers import _resolve_backend
from neuroconv.tools.nwb_helpers import (
    HDF5BackendConfiguration,
    configure_backend,
    make_or_load_nwbfile,
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

    def temporally_align_data_interfaces(
        self, metadata: Optional[dict] = None, conversion_options: Optional[dict] = None
    ) -> None:
        """Align timestamps between data interfaces.

        It is called by run_conversion() after the data interfaces have been initialized but before the data is added
        to the NWB file.
        In its current implementation, this method aligns timestamps between the behavior and video data interfaces.
        """
        behavior_interface = self.data_interface_objects["Behavior"]
        behavior_file_path = Path(behavior_interface.source_data["file_path"])
        file = read_mat(behavior_file_path)
        cam1_timestamps, cam2_timestamps = file["continuous"]["cam"]["time"]
        if conversion_options["Behavior"].get("normalize_timestamps", False):
            starting_timestamp = file["continuous"][metadata["Behavior"]["TimeSeries"][0]["name"]]["time"][0]
            cam1_timestamps -= starting_timestamp
            cam2_timestamps -= starting_timestamp
        self.data_interface_objects["VideoCamera1"].set_aligned_timestamps([cam1_timestamps])
        self.data_interface_objects["VideoCamera2"].set_aligned_timestamps([cam2_timestamps])

    # NOTE: run_conversion is copy-pasted from neuroconv.NWBConverter and only modified to call
    # temporally_align_data_interfaces with the correct arguments. This is a temporary solution until the neuroconv
    # library is updated to allow for easier customization of the conversion process
    # (see https://github.com/catalystneuro/neuroconv/pull/1162).
    def run_conversion(
        self,
        nwbfile_path: Optional[FilePath] = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        overwrite: bool = False,
        backend: Optional[Literal["hdf5"]] = None,
        backend_configuration: Optional[HDF5BackendConfiguration] = None,
        conversion_options: Optional[dict] = None,
    ) -> None:

        if nwbfile_path is None:
            warnings.warn(  # TODO: remove on or after 2024/12/26
                "Using Converter.run_conversion without specifying nwbfile_path is deprecated. To create an "
                "NWBFile object in memory, use Converter.create_nwbfile. To append to an existing NWBFile object,"
                " use Converter.add_to_nwbfile."
            )

        backend = _resolve_backend(backend, backend_configuration)
        no_nwbfile_provided = nwbfile is None  # Otherwise, variable reference may mutate later on inside the context

        file_initially_exists = Path(nwbfile_path).exists() if nwbfile_path is not None else False
        append_mode = file_initially_exists and not overwrite

        if metadata is None:
            metadata = self.get_metadata()

        self.validate_metadata(metadata=metadata, append_mode=append_mode)
        self.validate_conversion_options(conversion_options=conversion_options)

        self.temporally_align_data_interfaces(metadata=metadata, conversion_options=conversion_options)

        with make_or_load_nwbfile(
            nwbfile_path=nwbfile_path,
            nwbfile=nwbfile,
            metadata=metadata,
            overwrite=overwrite,
            backend=backend,
            verbose=getattr(self, "verbose", False),
        ) as nwbfile_out:
            if no_nwbfile_provided:
                self.add_to_nwbfile(nwbfile=nwbfile_out, metadata=metadata, conversion_options=conversion_options)

            if backend_configuration is None:
                backend_configuration = self.get_default_backend_configuration(nwbfile=nwbfile_out, backend=backend)

            configure_backend(nwbfile=nwbfile_out, backend_configuration=backend_configuration)
