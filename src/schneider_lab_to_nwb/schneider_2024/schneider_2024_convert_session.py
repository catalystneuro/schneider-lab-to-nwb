"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from zoneinfo import ZoneInfo
import shutil
import numpy as np

from neuroconv.utils import load_dict_from_file, dict_deep_update
from schneider_lab_to_nwb.schneider_2024 import Schneider2024NWBConverter


def session_to_nwb(
    recording_folder_path: str | Path,
    sorting_folder_path: str | Path,
    behavior_file_path: str | Path,
    video_folder_path: str | Path,
    intrinsic_signal_optical_imaging_folder_path: str | Path,
    output_dir_path: str | Path,
    stub_test: bool = False,
):
    recording_folder_path = Path(recording_folder_path)
    sorting_folder_path = Path(sorting_folder_path)
    behavior_file_path = Path(behavior_file_path)
    video_folder_path = Path(video_folder_path)
    intrinsic_signal_optical_imaging_folder_path = Path(intrinsic_signal_optical_imaging_folder_path)
    output_dir_path = Path(output_dir_path)
    video_file_paths = [
        file_path for file_path in video_folder_path.glob("*.mp4") if not file_path.name.startswith("._")
    ]
    video_file_paths = sorted(video_file_paths)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    session_id = "sample_session"
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Recording
    stream_name = "Signals CH"  # stream_names = ["Signals CH", "Signals AUX"]
    source_data.update(dict(Recording=dict(folder_path=recording_folder_path, stream_name=stream_name)))
    conversion_options.update(dict(Recording=dict(stub_test=stub_test)))

    # Add Sorting
    source_data.update(dict(Sorting=dict(folder_path=sorting_folder_path)))
    conversion_options.update(dict(Sorting=dict()))

    # Add Behavior
    source_data.update(dict(Behavior=dict(file_path=behavior_file_path)))
    conversion_options.update(dict(Behavior=dict()))

    # Add Video(s)
    # for i, video_file_path in enumerate(video_file_paths):
    #     metadata_key_name = f"VideoCamera{i+1}"
    #     source_data.update({metadata_key_name: dict(file_paths=[video_file_path], metadata_key_name=metadata_key_name)})
    #     conversion_options.update({metadata_key_name: dict()})

    # Add Optogenetic
    # source_data.update(dict(Optogenetic=dict(file_path=behavior_file_path)))
    # conversion_options.update(dict(Optogenetic=dict()))

    # Add Intrinsic Signal Optical Imaging
    # source_data.update(dict(ISOI=dict(folder_path=intrinsic_signal_optical_imaging_folder_path)))
    # conversion_options.update(dict(ISOI=dict()))

    converter = Schneider2024NWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    EST = ZoneInfo("US/Eastern")
    metadata["NWBFile"]["session_start_time"] = metadata["NWBFile"]["session_start_time"].replace(tzinfo=EST)

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "schneider_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    metadata["Subject"]["subject_id"] = "a_subject_id"  # Modify here or in the yaml file
    conversion_options["Sorting"]["units_description"] = metadata["Sorting"]["units_description"]

    # Add electrode metadata
    channel_positions = np.load(sorting_folder_path / "channel_positions.npy")
    if True:  # stub_test: SWITCH BACK TO stub_test WHEN ALL CHANNELS ARE PRESENT
        channel_positions = channel_positions[:1, :]
    location = metadata["Ecephys"]["ElectrodeGroup"][0]["location"]
    channel_ids = converter.data_interface_objects["Recording"].recording_extractor.get_channel_ids()
    converter.data_interface_objects["Recording"].recording_extractor.set_channel_locations(
        channel_ids=channel_ids, locations=channel_positions
    )
    converter.data_interface_objects["Recording"].recording_extractor.set_property(
        key="brain_area",
        ids=channel_ids,
        values=[location] * len(channel_ids),
    )
    converter.data_interface_objects["Recording"].recording_extractor._recording_segments[0].t_start = 0.0
    metadata["Ecephys"]["Device"] = editable_metadata["Ecephys"]["Device"]

    # # Overwrite video metadata
    # for i, video_file_path in enumerate(video_file_paths):
    #     metadata_key_name = f"VideoCamera{i+1}"
    #     metadata["Behavior"][metadata_key_name] = editable_metadata["Behavior"][metadata_key_name]

    # Run conversion
    from time import time

    start = time()
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)
    stop = time()
    print(f"Conversion took {stop-start:.2f} seconds")


def main():
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Schneider/Grant Zempolich Project Data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Schneider/conversion_nwb")
    stub_test = False

    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)

    # Example Session A1 Ephys + Behavior
    recording_folder_path = data_dir_path / "A1_EphysFiles" / "m53" / "Day1_A1"
    sorting_folder_path = recording_folder_path
    behavior_file_path = data_dir_path / "A1_EphysBehavioralFiles" / "raw_m53_231029_001.mat"
    video_folder_path = Path("")
    intrinsic_signal_optical_imaging_folder_path = Path("")
    session_to_nwb(
        recording_folder_path=recording_folder_path,
        sorting_folder_path=sorting_folder_path,
        behavior_file_path=behavior_file_path,
        video_folder_path=video_folder_path,
        intrinsic_signal_optical_imaging_folder_path=intrinsic_signal_optical_imaging_folder_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )


if __name__ == "__main__":
    main()
