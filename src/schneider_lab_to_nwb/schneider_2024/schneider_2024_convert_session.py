"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import datetime
from zoneinfo import ZoneInfo
import shutil
from pprint import pprint

from neuroconv.utils import load_dict_from_file, dict_deep_update
from schneider_lab_to_nwb.schneider_2024 import Schneider2024NWBConverter


def session_to_nwb(data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], stub_test: bool = False):

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)
    recording_folder_path = data_dir_path / "Raw Ephys" / "m69_2023-10-31_17-24-15_Day1_A1_stubbed"
    sorting_folder_path = data_dir_path / "Processed Ephys" / "m69_2023-10-31_17-24-15_Day1_A1"

    session_id = "sample_session"
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Recording
    stream_name = "Signals CH" # stream_names = ["Signals CH", "Signals AUX"]
    source_data.update(dict(Recording=dict(folder_path=recording_folder_path, stream_name=stream_name)))
    conversion_options.update(dict(Recording=dict(stub_test=stub_test)))

    # Add Sorting
    source_data.update(dict(Sorting=dict(folder_path=sorting_folder_path)))
    conversion_options.update(dict(Sorting=dict()))

    # # Add Behavior
    # source_data.update(dict(Behavior=dict()))
    # conversion_options.update(dict(Behavior=dict()))

    converter = Schneider2024NWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    date = datetime.datetime.today()  # TODO: Get this from author
    metadata["NWBFile"]["session_start_time"] = date

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "schneider_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    metadata["Subject"]["subject_id"] = "a_subject_id"  # Modify here or in the yaml file

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)

def main():
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Schneider/Schneider sample Data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Schneider/conversion_nwb")
    stub_test = False

    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )

if __name__ == "__main__":
    main()
