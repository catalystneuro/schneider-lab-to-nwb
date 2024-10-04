"""Primary class for converting intrinsic signal optical imaging."""
from pynwb.file import NWBFile
from pynwb.base import Images
from pynwb.image import GrayscaleImage, RGBImage
from pydantic import FilePath, DirectoryPath
import numpy as np
from PIL import Image

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict, get_base_schema
from neuroconv.tools import nwb_helpers


class Schneider2024IntrinsicSignalOpticalImagingInterface(BaseDataInterface):
    """Intrinsic signal optical imaging interface for schneider_2024 conversion"""

    keywords = ["intrinsic signal optical imaging"]

    def __init__(self, folder_path: DirectoryPath):
        super().__init__(folder_path=folder_path)

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # Read Data
        folder_path = self.source_data["folder_path"]
        raw_image_path = folder_path / "BloodvesselPattern.tiff"
        processed_image_path = folder_path / "IOS_imageOverlaidFinal.jpg"
        with Image.open(raw_image_path) as image:
            raw_image_array = np.array(image)
        with Image.open(processed_image_path) as image:
            processed_image_array = np.array(image)

        # Add Data to NWBFile
        isoi_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name="intrinsic_signal_optical_imaging",
            description="For precise targeting of auditory cortex, intrinsic optical imaging (IOS) will be performed using a 2-photon microscope (Neurolabware). The skull is first bilaterally thinned over a region of interest (ROI) and made translucent. On experiment day, 680nm red light (ThorLabs) is used to image the ROI. Data is collected via MATLAB running custom suites for online and offline analyses.",
        )
        raw_image = GrayscaleImage(
            name="raw_image",
            data=raw_image_array,
            description="Original image capture of ROI for intrinsic imaging.",
        )
        processed_image = RGBImage(
            name="processed_image",
            data=processed_image_array,
            description="Original image capture of ROI overlaid with topographic map of processed intrinsic signal.",
        )
        images = Images(
            name="images",
            description="Intrinsic signal optical images.",
            images=[raw_image, processed_image],
        )
        isoi_module.add(images)
