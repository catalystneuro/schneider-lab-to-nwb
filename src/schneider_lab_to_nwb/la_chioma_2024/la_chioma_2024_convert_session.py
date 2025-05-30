"""Primary conversion script for the La Chioma 2024 dataset."""
from pathlib import Path
from zoneinfo import ZoneInfo
import shutil
from pydantic import DirectoryPath, FilePath

from neuroconv.utils import load_dict_from_file, dict_deep_update
from schneider_lab_to_nwb.la_chioma_2024 import LaChioma2024NWBConverter


def session_to_nwb(
    behavior_file_path: FilePath,
    output_dir_path: DirectoryPath,
    ephys_folder_path: DirectoryPath | None = None,
    ap_stream_name: str | None = None,
    stub_test: bool = False,
    verbose: bool = True,
):
    """
    Convert a session to NWB format.

    Parameters
    ----------
    ephys_folder_path : DirectoryPath
        Path to the folder containing electrophysiology data if available.
    ap_stream_name : str
        The stream name that corresponds to the raw recording if available. (e.g. "Record Node 102#Neuropix-PXI-100.ProbeA")
    behavior_file_path : FilePath
        Path to the behavior .mat file.
    output_dir_path : DirectoryPath
        Path to output directory.
    stub_test : bool, default: False
        If True, truncates data for testing.
    verbose : bool, default: True
        If True, prints progress information.
    """
    output_dir_path = Path(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    source_data = dict()
    conversion_options = dict()

    # Add Ephys Recording
    if ephys_folder_path is not None:
        if ap_stream_name is None:
            raise ValueError("'ap_stream_name' must be provided when recording is available.")
        ephys_folder_path = Path(ephys_folder_path)
        source_data.update(
            dict(Recording=dict(folder_path=ephys_folder_path, stream_name=ap_stream_name, verbose=verbose))
        )
        conversion_options.update(dict(Recording=dict(stub_test=stub_test)))

    # Add Behavior
    source_data.update(dict(Behavior=dict(file_path=behavior_file_path)))
    conversion_options.update(dict(Behavior=dict()))

    # Initialize converter
    converter = LaChioma2024NWBConverter(source_data=source_data, verbose=verbose)
    metadata = converter.get_metadata()

    # Add timezone for session start time
    # TODO: how to figure out the session_start_time for sessions without ephys data?
    session_start_time = metadata["NWBFile"]["session_start_time"]
    session_start_time = session_start_time.replace(tzinfo=ZoneInfo("US/Eastern"))
    metadata["NWBFile"].update(session_start_time=session_start_time)

    # Load metadata
    editable_metadata_path = Path(__file__).parent / "la_chioma_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Update metadata with session_id
    behavior_file_path = Path(behavior_file_path)
    subject_id, session_id, _ = behavior_file_path.stem.split("_")
    metadata["NWBFile"].update(session_id=session_id)
    metadata["Subject"].update(subject_id=subject_id)

    nwbfile_path = Path(output_dir_path) / f"sub-{subject_id}_ses-{session_id}.nwb"
    # Run conversion
    converter.run_conversion(
        metadata=metadata,
        nwbfile_path=nwbfile_path,
        conversion_options=conversion_options,
    )


def main():
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T9/data/Alessandro La Chioma Project Data")
    output_dir_path = Path("/Users/weian/data") / "nwbfiles"
    stub_test = True
    verbose = True

    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)

    # Example Session with ephys data
    session_dir_path = data_dir_path / "Example dataset processed files - AL240404c 2024-04-22"
    ephys_folder_path = session_dir_path / "DataEphys" / "AL240404c_2024-04-22_17-45-19" / "Record Node 102"
    # The stream name that corresponds to the raw recording
    ap_stream_name = "Record Node 102#Neuropix-PXI-100.ProbeA"

    processed_behavior_file_path = session_dir_path / "AL240404c_2024-04-22_syncedData.mat"
    session_to_nwb(
        ephys_folder_path=ephys_folder_path,
        ap_stream_name=ap_stream_name,
        behavior_file_path=processed_behavior_file_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        verbose=verbose,
    )


if __name__ == "__main__":
    main()
