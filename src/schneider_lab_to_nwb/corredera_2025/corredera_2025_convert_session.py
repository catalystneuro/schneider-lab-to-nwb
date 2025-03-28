"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from zoneinfo import ZoneInfo
import shutil
from datetime import datetime
from typing import Optional, Literal
from pydantic import FilePath, DirectoryPath

from neuroconv.utils import load_dict_from_file, dict_deep_update
from schneider_lab_to_nwb.corredera_2025 import Corredera2025NWBConverter


def session_to_nwb(
    output_dir_path: DirectoryPath,
    ephys_folder_path: DirectoryPath,
    video_file_path: FilePath,
    stub_test: bool = False,
    verbose: bool = True,
):
    """Convert a session of data to NWB format.

    Parameters
    ----------
    behavior_file_path : FilePath
        Path to the behavior .mat file.
    video_folder_path : DirectoryPath
        Path to the folder containing the video files.
    intrinsic_signal_optical_imaging_folder_path : DirectoryPath
        Path to the folder containing the intrinsic signal optical imaging files.
    output_dir_path : DirectoryPath
        Path to the directory where the output NWB file will be saved.
    ephys_folder_path : Optional[DirectoryPath], optional
        Path to the folder containing electrophysiology data, by default None.
    has_opto : bool, optional
        Whether the session includes optogenetic data, by default False.
    brain_region : Literal["A1", "M2"], optional
        Brain region of interest, by default "A1".
    stub_test : bool, optional
        Whether to run in stub test mode, by default False.
    verbose : bool, optional
        Whether to print verbose output, by default True.
    """
    ephys_folder_path = Path(ephys_folder_path)
    output_dir_path = Path(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    source_data = dict()
    conversion_options = dict()

    # Add Ephys Recording and Sorting
    # stream_name = "Signals CH"
    # source_data.update(dict(Recording=dict(folder_path=ephys_folder_path, stream_name=stream_name, verbose=verbose)))
    # conversion_options.update(dict(Recording=dict(stub_test=stub_test)))
    # source_data.update(dict(Sorting=dict(folder_path=ephys_folder_path, verbose=verbose)))
    # conversion_options.update(dict(Sorting=dict()))

    # Add Video
    source_data.update(dict(Video=dict(file_paths=[video_file_path], verbose=verbose)))
    conversion_options.update(dict(Video=dict()))

    converter = Corredera2025NWBConverter(source_data=source_data, verbose=verbose)
    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "corredera_2025_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # conversion_options["Sorting"]["units_description"] = metadata["Sorting"]["units_description"]

    subject_id = "m14"  # TODO: Get subject_id
    session_id = "2024-12-12"  # TODO: Get session_id
    nwbfile_path = output_dir_path / f"sub-{subject_id}_ses-{session_id}.nwb"
    metadata["NWBFile"]["session_id"] = session_id
    metadata["Subject"]["subject_id"] = subject_id

    # Add session start time to metadata
    split_name = video_file_path.stem.split("_")
    session_start_time = datetime.strptime(f"{split_name[-2]}_{split_name[-1]}", "%Y%m%d_%H%M%S")
    EST = ZoneInfo("US/Eastern")
    metadata["NWBFile"]["session_start_time"] = session_start_time.replace(tzinfo=EST)

    # Add subject info to metadata
    metadata["Subject"]["sex"] = "U"  # TODO: Get sex

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


def main():
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Schneider/Ariadna Corredera Project Data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Schneider/conversion_nwb/corredera_2025")
    stub_test = True
    verbose = True

    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)

    # Example Session
    ephys_folder_path = data_dir_path
    video_file_path = data_dir_path / "m14_pb_2024-12-12_001_CamFlir1_20241212_102813.avi"
    session_to_nwb(
        ephys_folder_path=ephys_folder_path,
        video_file_path=video_file_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        verbose=verbose,
    )


if __name__ == "__main__":
    main()
