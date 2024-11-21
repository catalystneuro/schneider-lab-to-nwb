"""Primary class for converting intrinsic signal optical imaging."""
from pynwb.file import NWBFile
from pynwb.base import Images
from pynwb.image import GrayscaleImage, RGBImage
from pynwb.device import Device
from pydantic import DirectoryPath
import numpy as np
from PIL import Image

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools import nwb_helpers


class Zempolich2024IntrinsicSignalOpticalImagingInterface(BaseDataInterface):
    """Intrinsic signal optical imaging interface for schneider_2024 conversion"""

    keywords = ("intrinsic signal optical imaging",)

    def __init__(self, folder_path: DirectoryPath):
        """Initialize the intrinsic signal optical imaging interface.

        Parameters
        ----------
        folder_path : DirectoryPath
            Path to the folder containing the intrinsic signal optical imaging files.
        """
        super().__init__(folder_path=folder_path)

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["IntrinsicSignalOpticalImaging"] = dict()
        metadata_schema["properties"]["IntrinsicSignalOpticalImaging"]["properties"] = {
            "Module": {
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
            "Images": {
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
            "RawImage": {
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
            "ProcessedImage": {
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        }
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
        isoi_metadata = metadata["IntrinsicSignalOpticalImaging"]
        isoi_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name=isoi_metadata["Module"]["name"],
            description=isoi_metadata["Module"]["description"],
        )
        raw_image = GrayscaleImage(
            name=isoi_metadata["RawImage"]["name"],
            data=raw_image_array,
            description=isoi_metadata["RawImage"]["description"],
        )
        processed_image = RGBImage(
            name=isoi_metadata["ProcessedImage"]["name"],
            data=processed_image_array,
            description=isoi_metadata["ProcessedImage"]["description"],
        )
        images = Images(
            name=isoi_metadata["Images"]["name"],
            description=isoi_metadata["Images"]["description"],
            images=[raw_image, processed_image],
        )
        isoi_module.add(images)

        # Add Devices
        for device_kwargs in isoi_metadata["Devices"]:
            device = Device(**device_kwargs)
            nwbfile.add_device(device)
