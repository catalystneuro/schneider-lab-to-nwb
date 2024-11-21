"""Primary script to run to convert all sessions in a dataset using session_to_nwb."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from pprint import pformat
import traceback
from tqdm import tqdm
import shutil

from schneider_lab_to_nwb.zempolich_2024.zempolich_2024_convert_session import session_to_nwb


def dataset_to_nwb(
    *,
    data_dir_path: str | Path,
    output_dir_path: str | Path,
    max_workers: int = 1,
    verbose: bool = True,
):
    """Convert the entire dataset to NWB.

    Parameters
    ----------
    data_dir_path : str | Path
        The path to the directory containing the raw data.
    output_dir_path : str | Path
        The path to the directory where the NWB files will be saved.
    max_workers : int, optional
        The number of workers to use for parallel processing, by default 1
    verbose : bool, optional
        Whether to print verbose output, by default True
    """
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    session_to_nwb_kwargs_per_session = get_session_to_nwb_kwargs_per_session(data_dir_path=data_dir_path)

    futures = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for session_to_nwb_kwargs in session_to_nwb_kwargs_per_session:
            session_to_nwb_kwargs["output_dir_path"] = output_dir_path
            session_to_nwb_kwargs["verbose"] = verbose
            nwbfile_name = get_nwbfile_name_from_kwargs(session_to_nwb_kwargs)
            exception_file_path = output_dir_path / f"ERROR_{nwbfile_name}.txt"
            futures.append(
                executor.submit(
                    safe_session_to_nwb,
                    session_to_nwb_kwargs=session_to_nwb_kwargs,
                    exception_file_path=exception_file_path,
                )
            )
        for _ in tqdm(as_completed(futures), total=len(futures)):
            pass


def get_nwbfile_name_from_kwargs(session_to_nwb_kwargs: dict) -> str:
    """Get the name of the NWB file from the session_to_nwb kwargs.

    Parameters
    ----------
    session_to_nwb_kwargs : dict
        The arguments for session_to_nwb.

    Returns
    -------
    str
        The name of the NWB file that would be created by running session_to_nwb(**session_to_nwb_kwargs).
    """
    behavior_file_path = session_to_nwb_kwargs["behavior_file_path"]
    subject_id = behavior_file_path.name.split("_")[1]
    session_id = behavior_file_path.name.split("_")[2]
    nwbfile_name = f"sub-{subject_id}_ses-{session_id}.nwb"
    return nwbfile_name


def safe_session_to_nwb(*, session_to_nwb_kwargs: dict, exception_file_path: str | Path):
    """Convert a session to NWB while handling any errors by recording error messages to the exception_file_path.

    Parameters
    ----------
    session_to_nwb_kwargs : dict
        The arguments for session_to_nwb.
    exception_file_path : Path
        The path to the file where the exception messages will be saved.
    """
    exception_file_path = Path(exception_file_path)
    try:
        session_to_nwb(**session_to_nwb_kwargs)
    except Exception as e:
        with open(exception_file_path, mode="w") as f:
            f.write(f"session_to_nwb_kwargs: \n {pformat(session_to_nwb_kwargs)}\n\n")
            f.write(traceback.format_exc())


def get_session_to_nwb_kwargs_per_session(*, data_dir_path: str | Path):
    """Get the kwargs for session_to_nwb for each session in the dataset.

    Parameters
    ----------
    data_dir_path : str | Path
        The path to the directory containing the raw data.

    Returns
    -------
    list[dict[str, Any]]
        A list of dictionaries containing the kwargs for session_to_nwb for each session.
    """
    a1_ephys_path = data_dir_path / "A1_EphysFiles"
    a1_ephys_behavior_path = data_dir_path / "A1_EphysBehavioralFiles"
    a1_opto_path = data_dir_path / "A1_OptoBehavioralFiles"
    m2_ephys_path = data_dir_path / "M2_EphysFiles"
    m2_ephys_behavior_path = data_dir_path / "M2_EphysBehavioralFiles"
    m2_opto_path = data_dir_path / "M2_OptoBehavioralFiles"

    a1_kwargs = get_brain_region_kwargs(
        ephys_path=a1_ephys_path,
        ephys_behavior_path=a1_ephys_behavior_path,
        opto_path=a1_opto_path,
        brain_region="A1",
    )
    m2_kwargs = get_brain_region_kwargs(
        ephys_path=m2_ephys_path,
        ephys_behavior_path=m2_ephys_behavior_path,
        opto_path=m2_opto_path,
        brain_region="M2",
    )
    session_to_nwb_kwargs_per_session = a1_kwargs + m2_kwargs

    return session_to_nwb_kwargs_per_session


def get_brain_region_kwargs(ephys_path, ephys_behavior_path, opto_path, brain_region):
    """Get the session_to_nwb kwargs for each session in the dataset for a given brain region.

    Parameters
    ----------
    ephys_path : pathlib.Path
        Path to the directory containing electrophysiology data for subjects.
    ephys_behavior_path : pathlib.Path
        Path to the directory containing electrophysiology behavior data files.
    opto_path : pathlib.Path
        Path to the directory containing optogenetics behavior data files.
    brain_region : str
        The brain region associated with the sessions.

    Returns
    -------
    list[dict[str, Any]]
        A list of dictionaries containing the kwargs for session_to_nwb for each session in the dataset within a specific brain region.
    """
    session_to_nwb_kwargs_per_session = []
    for subject_dir in ephys_path.iterdir():
        subject_id = subject_dir.name
        matched_behavior_paths = sorted(ephys_behavior_path.glob(f"raw_{subject_id}_*.mat"))
        sorted_session_dirs = sorted(subject_dir.iterdir())
        for ephys_folder_path, behavior_file_path in zip(sorted_session_dirs, matched_behavior_paths):
            session_to_nwb_kwargs = dict(
                ephys_folder_path=ephys_folder_path,
                behavior_file_path=behavior_file_path,
                brain_region=brain_region,
                intrinsic_signal_optical_imaging_folder_path="",  # TODO: Add intrinsic signal optical imaging folder path
                video_folder_path="",  # TODO: Add video folder path
            )
            session_to_nwb_kwargs_per_session.append(session_to_nwb_kwargs)
    for behavior_file_path in opto_path.iterdir():
        session_to_nwb_kwargs = dict(
            behavior_file_path=behavior_file_path,
            brain_region=brain_region,
            has_opto=True,
            intrinsic_signal_optical_imaging_folder_path="",  # TODO: Add intrinsic signal optical imaging folder path
            video_folder_path="",  # TODO: Add video folder path
        )
        session_to_nwb_kwargs_per_session.append(session_to_nwb_kwargs)
    return session_to_nwb_kwargs_per_session


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Schneider/Grant Zempolich Project Data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Schneider/conversion_nwb")
    max_workers = 4
    if output_dir_path.exists():
        shutil.rmtree(
            output_dir_path, ignore_errors=True
        )  # ignore errors due to MacOS race condition (https://github.com/python/cpython/issues/81441)

    dataset_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        max_workers=max_workers,
        verbose=False,
    )
