"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from zoneinfo import ZoneInfo
import shutil
import numpy as np
from datetime import datetime
from typing import Optional

from neuroconv.utils import load_dict_from_file, dict_deep_update
from schneider_lab_to_nwb.zempolich_2024 import Zempolich2024NWBConverter


def session_to_nwb(
    behavior_file_path: str | Path,
    video_folder_path: str | Path,
    intrinsic_signal_optical_imaging_folder_path: str | Path,
    output_dir_path: str | Path,
    ephys_folder_path: Optional[str | Path] = None,
    has_opto: bool = False,
    stub_test: bool = False,
):
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
    if ephys_folder_path is None:
        has_ephys = False
    else:
        has_ephys = True
        ephys_folder_path = Path(ephys_folder_path)

    source_data = dict()
    conversion_options = dict()

    # Add Ephys Recording and Sorting
    if has_ephys:
        stream_name = "Signals CH"
        source_data.update(dict(Recording=dict(folder_path=ephys_folder_path, stream_name=stream_name)))
        conversion_options.update(dict(Recording=dict(stub_test=stub_test)))

        source_data.update(dict(Sorting=dict(folder_path=ephys_folder_path)))
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
    if has_opto:
        source_data.update(dict(Optogenetic=dict(file_path=behavior_file_path)))
        conversion_options.update(dict(Optogenetic=dict()))

    # Add Intrinsic Signal Optical Imaging
    # source_data.update(dict(ISOI=dict(folder_path=intrinsic_signal_optical_imaging_folder_path)))
    # conversion_options.update(dict(ISOI=dict()))

    converter = Zempolich2024NWBConverter(source_data=source_data)
    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "schneider_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)
    if has_ephys:
        folder_name = (
            source_data["Recording"]["folder_path"].parent.name + "/" + source_data["Recording"]["folder_path"].name
        )
        folder_name_to_start_datetime = metadata["Ecephys"].pop("folder_name_to_start_datetime")
        if folder_name in folder_name_to_start_datetime.keys():
            metadata["NWBFile"]["session_start_time"] = datetime.fromisoformat(
                folder_name_to_start_datetime[folder_name]
            )
    else:
        metadata["NWBFile"]["session_start_time"] = datetime.strptime(behavior_file_path.name.split("_")[2], "%y%m%d")

    # Add datetime to conversion
    EST = ZoneInfo("US/Eastern")
    metadata["NWBFile"]["session_start_time"] = metadata["NWBFile"]["session_start_time"].replace(tzinfo=EST)

    metadata["Subject"]["subject_id"] = "a_subject_id"  # Modify here or in the yaml file
    if has_ephys:
        conversion_options["Sorting"]["units_description"] = metadata["Sorting"]["units_description"]

    # Add electrode metadata
    if has_ephys:
        channel_positions = np.load(ephys_folder_path / "channel_positions.npy")
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

    subject_id = behavior_file_path.name.split("_")[1]
    session_id = behavior_file_path.name.split("_")[2]
    nwbfile_path = output_dir_path / f"sub-{subject_id}_ses-{session_id}.nwb"
    metadata["NWBFile"]["session_id"] = session_id
    metadata["Subject"]["subject_id"] = subject_id

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


def main():
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Schneider/Grant Zempolich Project Data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Schneider/conversion_nwb")
    stub_test = False

    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)

    # Example Session A1 Ephys + Behavior
    ephys_folder_path = data_dir_path / "A1_EphysFiles" / "m53" / "Day1_A1"
    behavior_file_path = data_dir_path / "A1_EphysBehavioralFiles" / "raw_m53_231029_001.mat"
    video_folder_path = Path("")
    intrinsic_signal_optical_imaging_folder_path = Path("")
    session_to_nwb(
        ephys_folder_path=ephys_folder_path,
        behavior_file_path=behavior_file_path,
        video_folder_path=video_folder_path,
        intrinsic_signal_optical_imaging_folder_path=intrinsic_signal_optical_imaging_folder_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )

    # Example Session A1 Ogen + Behavior
    behavior_file_path = data_dir_path / "A1_OptoBehavioralFiles" / "raw_m53_231013_001.mat"
    video_folder_path = Path("")
    intrinsic_signal_optical_imaging_folder_path = Path("")
    session_to_nwb(
        behavior_file_path=behavior_file_path,
        video_folder_path=video_folder_path,
        intrinsic_signal_optical_imaging_folder_path=intrinsic_signal_optical_imaging_folder_path,
        output_dir_path=output_dir_path,
        has_opto=True,
        stub_test=stub_test,
    )


if __name__ == "__main__":
    main()
