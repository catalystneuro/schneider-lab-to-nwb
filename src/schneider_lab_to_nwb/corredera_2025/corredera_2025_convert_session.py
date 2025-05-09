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
    raw_ephys_file_path: FilePath,
    processed_ephys_file_path: FilePath,
    sorting_folder_path: DirectoryPath,
    video_file_path: FilePath,
    sleap_file_path: FilePath,
    audio_file_path: FilePath,
    stimulus_file_path: FilePath,
    session_type: Literal["natural_exploration", "vr_exploration", "playback", "loom_threat"],
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
    raw_ephys_file_path = Path(raw_ephys_file_path)
    processed_ephys_file_path = Path(processed_ephys_file_path)
    sorting_folder_path = Path(sorting_folder_path)
    video_file_path = Path(video_file_path)
    sleap_file_path = Path(sleap_file_path)
    output_dir_path = Path(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    source_data = dict()
    conversion_options = dict()

    # Add Ephys Recording
    num_channels = 64
    sampling_frequency = 25_000.0
    source_data.update(
        dict(
            RawRecording=dict(
                file_path=raw_ephys_file_path,
                num_channels=num_channels,
                sampling_frequency=sampling_frequency,
                verbose=verbose,
                es_key="ElectricalSeriesRaw",
            ),
            ProcessedRecording=dict(
                file_path=processed_ephys_file_path,
                num_channels=num_channels,
                sampling_frequency=sampling_frequency,
                verbose=verbose,
                es_key="ElectricalSeriesProcessed",
            ),
        )
    )
    conversion_options.update(
        dict(
            RawRecording=dict(stub_test=stub_test),
            ProcessedRecording=dict(stub_test=stub_test, write_as="processed"),
        )
    )

    # Add Sorting
    source_data.update(dict(Sorting=dict(folder_path=sorting_folder_path, verbose=verbose)))
    conversion_options.update(dict(Sorting=dict()))

    # Add Video
    source_data.update(dict(Video=dict(file_paths=[video_file_path], verbose=verbose, video_name="VideoFLIR")))
    conversion_options.update(dict(Video=dict()))

    # Add Audio
    source_data.update(dict(Audio=dict(file_path=audio_file_path)))
    conversion_options.update(dict(Audio=dict(stub_test=stub_test)))

    # Add Stimulus
    source_data.update(dict(Stimulus=dict(file_path=stimulus_file_path)))
    conversion_options.update(dict(Stimulus=dict()))

    # Add SLEAP
    source_data.update(dict(SLEAP=dict(file_path=sleap_file_path, video_file_path=video_file_path, verbose=verbose)))
    conversion_options.update(dict(SLEAP=dict()))

    converter = Corredera2025NWBConverter(source_data=source_data, verbose=verbose)
    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "corredera_2025_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    conversion_options["Sorting"]["units_description"] = metadata["Sorting"]["units_description"]

    session_id = metadata["NWBFile"]["session_id"]
    subject_id = metadata["Subject"]["subject_id"]
    nwbfile_path = output_dir_path / f"sub-{subject_id}_ses-{session_id}.nwb"

    # Add session start time to metadata
    split_name = video_file_path.stem.split("_")
    session_start_time = datetime.strptime(f"{split_name[-2]}_{split_name[-1]}", "%Y%m%d_%H%M%S")
    EST = ZoneInfo("US/Eastern")
    metadata["NWBFile"]["session_start_time"] = session_start_time.replace(tzinfo=EST)

    # Add subject and session info to metadata
    metadata["Subject"]["sex"] = metadata["SubjectMaps"]["subject_id_to_sex"][subject_id]
    session_metadata = next(meta for meta in metadata["Session"] if meta["name"] == session_type)
    session_description = session_metadata["description"]
    metadata["NWBFile"]["session_description"] = session_description

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

    # Example Session w/o visual stimulus
    session_dir_path = data_dir_path / "example_data_ari_01"
    raw_ephys_file_path = session_dir_path / "HSW_2024_12_12__10_28_23__70min_17sec__hsamp_64ch_25000sps.bin"
    processed_ephys_file_path = (
        session_dir_path / "preKS_HSW_2024_12_12__10_28_23__70min_17sec__hsamp_64ch_25000sps.bin"
    )
    sorting_folder_path = session_dir_path / "kilosort4_curated"
    video_file_path = session_dir_path / "m14_pb_2024-12-12_001_CamFlir1_20241212_102813.avi"
    audio_file_path = session_dir_path / "m14_pb_2024-12-12_001_micrec.mic"
    sleap_file_path = session_dir_path / "labels.v002.slp.241216_121950.predictions.slp"
    stimulus_file_path = session_dir_path / "m14_pb_2024-12-12_001_data.mat"
    session_type = "loom_threat"
    session_to_nwb(
        ephys_folder_path=ephys_folder_path,
        video_file_path=video_file_path,
        audio_file_path=audio_file_path,
        sleap_file_path=sleap_file_path,
        stimulus_file_path=stimulus_file_path,
        output_dir_path=output_dir_path,
        session_type=session_type,
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session w/ visual stimulus
    session_dir_path = data_dir_path / "example_data_ari_02"
    ephys_folder_path = session_dir_path
    video_file_path = session_dir_path / "m14_vr_threat_2024-12-12_001_CamFlir1_20241212_120339.avi"
    audio_file_path = session_dir_path / "m14_vr_threat_2024-12-12_001_micrec.mic"
    sleap_file_path = session_dir_path / "labels.v001.slp.241216_143124.predictions.slp"
    stimulus_file_path = session_dir_path / "m14_vr_threat_2024-12-12_001_data.mat"
    session_type = "loom_threat"
    session_to_nwb(
        raw_ephys_file_path=raw_ephys_file_path,
        processed_ephys_file_path=processed_ephys_file_path,
        sorting_folder_path=sorting_folder_path,
        video_file_path=video_file_path,
        audio_file_path=audio_file_path,
        sleap_file_path=sleap_file_path,
        stimulus_file_path=stimulus_file_path,
        output_dir_path=output_dir_path,
        session_type=session_type,
        stub_test=stub_test,
        verbose=verbose,
    )


if __name__ == "__main__":
    main()
