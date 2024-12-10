"""Primary class for converting intrinsic signal optical imaging."""
from pynwb.file import NWBFile
from pynwb.base import Images
from pynwb.image import RGBImage
from pynwb.device import Device
from pydantic import FilePath
import numpy as np
from PIL import Image
from pathlib import Path

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools import nwb_helpers


class Zempolich2024IntrinsicSignalOpticalImagingInterface(BaseDataInterface):
    """Intrinsic signal optical imaging interface for schneider_2024 conversion"""

    keywords = ("intrinsic signal optical imaging",)

    def __init__(self, overlaid_image_path: FilePath, target_image_path: FilePath):
        """Initialize the intrinsic signal optical imaging interface.

        Parameters
        ----------
        overlaid_image_path : FilePath
            Path to the intrinsic signal optical imaging overlaid image file.
        target_image_path : FilePath
            Path to the intrinsic signal optical imaging target image file.
        """
        super().__init__(overlaid_image_path=overlaid_image_path, target_image_path=target_image_path)

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
        overlaid_image_path = Path(self.source_data["overlaid_image_path"])
        target_image_path = Path(self.source_data["target_image_path"])
        with Image.open(overlaid_image_path) as image:
            overlaid_image_array = np.array(image)
        with Image.open(target_image_path) as image:
            target_image_array = np.array(image)

        # Add Data to NWBFile
        isoi_metadata = metadata["IntrinsicSignalOpticalImaging"]
        isoi_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name=isoi_metadata["Module"]["name"],
            description=isoi_metadata["Module"]["description"],
        )
        overlaid_image = RGBImage(
            name=isoi_metadata["OverlaidImage"]["name"],
            data=overlaid_image_array,
            description=isoi_metadata["OverlaidImage"]["description"],
        )
        target_image = RGBImage(
            name=isoi_metadata["TargetImage"]["name"],
            data=target_image_array,
            description=isoi_metadata["TargetImage"]["description"],
        )
        images = Images(
            name=isoi_metadata["Images"]["name"],
            description=isoi_metadata["Images"]["description"],
            images=[overlaid_image, target_image],
        )
        isoi_module.add(images)

        # Add Devices
        for device_kwargs in isoi_metadata["Devices"]:
            device = Device(**device_kwargs)
            nwbfile.add_device(device)
