"""Primary conversion script for the La Chioma 2024 dataset."""
from pathlib import Path
from zoneinfo import ZoneInfo
import shutil
from datetime import datetime
from typing import Optional, Literal
from pydantic import FilePath, DirectoryPath

from neuroconv.utils import load_dict_from_file, dict_deep_update
from schneider_lab_to_nwb.la_chioma_2024 import LaChioma2024NWBConverter


def session_to_nwb(
    ephys_folder_path: DirectoryPath,
    output_dir_path: DirectoryPath,
    stub_test: bool = False,
    verbose: bool = True,
):
    """
    Convert a session to NWB format.

    Parameters
    ----------
    ephys_folder_path : DirectoryPath
        Path to the folder containing electrophysiology data.
    output_dir_path : DirectoryPath
        Path to output directory.
    stub_test : bool, default: False
        If True, truncates data for testing.
    verbose : bool, default: True
        If True, prints progress information.
    """
    ephys_folder_path = Path(ephys_folder_path)
    output_dir_path = Path(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    source_data = dict()
    conversion_options = dict()

    # Add Ephys Recording and Sorting
    stream_name = "Record Node 102#Neuropix-PXI-100.ProbeA"
    source_data.update(dict(Recording=dict(folder_path=ephys_folder_path, stream_name=stream_name, verbose=verbose)))
    conversion_options.update(dict(Recording=dict(stub_test=stub_test)))

    # Initialize converter
    converter = LaChioma2024NWBConverter(source_data=source_data, verbose=verbose)
    metadata = converter.get_metadata()

    # Load metadata
    editable_metadata_path = Path(__file__).parent / "la_chioma_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Run conversion
    converter.run_conversion(
        metadata=metadata,
        nwbfile_path=str(output_dir_path / "la_chioma_2024_session.nwb"),
        conversion_options=conversion_options,
    )


if __name__ == "__main__":
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T9/data/Alessandro La Chioma Project Data")
    output_dir_path = data_dir_path / "nwbfiles"
    stub_test = True
    verbose = True

    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)

    # Example Session with ephys data
    session_dir_path = data_dir_path / "Example dataset processed files - AL240404c 2024-04-22"
    ephys_folder_path = session_dir_path / "DataEphys" / "AL240404c_2024-04-22_17-45-19" / "Record Node 102"
    session_to_nwb(
        ephys_folder_path=ephys_folder_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        verbose=verbose,
    )