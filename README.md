# schneider-lab-to-nwb
NWB conversion scripts for Schneider lab data to the [Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.

## Installation from Github
We recommend installing the package directly from Github. This option has the advantage that the source code can be modifed if you need to amend some of the code we originally provided to adapt to future experimental differences. To install the conversion from GitHub you will need to use `git` ([installation instructions](https://github.com/git-guides/install-git)). We also recommend the installation of `conda` ([installation instructions](https://docs.conda.io/en/latest/miniconda.html)) as it contains all the required machinery in a single and simple install.

From a terminal (note that conda should install one in your system) you can do the following:

```bash
git clone https://github.com/catalystneuro/schneider-lab-to-nwb
cd schneider-lab-to-nwb
conda env create --file make_env.yml
conda activate schneider_lab_to_nwb_env
```

This creates a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html) which isolates the conversion code from your system libraries.  We recommend that you run all your conversion related tasks and analysis from the created environment in order to minimize issues related to package dependencies.

If you fork this repository and are running code from that fork, instead use
```bash
git clone https://github.com/your_github_username/schneider-lab-to-nwb
```

Then you can run
```bash
cd schneider-lab-to-nwb
conda env create --file make_env.yml
conda activate schneider_lab_to_nwb_env
```

Alternatively, if you want to avoid conda altogether (for example if you use another virtual environment tool) you can install the repository with the following commands using only pip:

```bash
git clone https://github.com/catalystneuro/schneider-lab-to-nwb
cd schneider-lab-to-nwb
pip install -e .
```

Note:
both of the methods above install the repository in [editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs).
The dependencies for this environment are stored in the dependencies section of the `pyproject.toml` file.

## Helpful Definitions

This conversion project is comprised primarily by DataInterfaces, NWBConverters, and conversion scripts.

In neuroconv, a [DataInterface](https://neuroconv.readthedocs.io/en/main/user_guide/datainterfaces.html) is a class that specifies the procedure to convert a single data modality to NWB.
This is usually accomplished with a single read operation from a distinct set of files.
For example, in this conversion, the `Zempolich2024BehaviorInterface` contains the code that converts all of the behavioral data to NWB from a raw .mat file.

In neuroconv, a [NWBConverter](https://neuroconv.readthedocs.io/en/main/user_guide/nwbconverter.html) is a class that combines many data interfaces and specifies the relationships between them, such as temporal alignment.
This allows users to combine multiple modalites into a single NWB file in an efficient and modular way.

In this conversion project, the conversion scripts determine which sessions to convert,
instantiate the appropriate NWBConverter object,
and convert all of the specified sessions, saving them to an output directory of .nwb files.

## Repository structure
Each conversion is organized in a directory of its own in the `src` directory:

    schneider-lab-to-nwb/
    ├── LICENSE
    ├── MANIFEST.in
    ├── README.md
    ├── make_env.yml
    ├── pyproject.toml
    └── src
        └── schneider_lab_to_nwb
            ├── __init__.py
            ├── another_conversion
            └── zempolich_2024
                ├── __init__.py
                ├── zempolich_2024_behaviorinterface.py
                ├── zempolich_2024_convert_all_sessions.py
                ├── zempolich_2024_convert_session.py
                ├── zempolich_2024_intrinsic_signal_imaging_interface.py
                ├── zempolich_2024_metadata.yaml
                ├── zempolich_2024_notes.md
                ├── zempolich_2024_nwbconverter.py
                ├── zempolich_2024_open_ephys_recording_interface.py
                └── zempolich_2024_optogeneticinterface.py

For the conversion `zempolich_2024` you can find a directory located in `src/schneider-lab-to-nwb/zempolich_2024`. Inside that conversion directory you can find the following files:

* `__init__.py` : This init file imports all the datainterfaces and NWBConverters so that they can be accessed directly from schneider_lab_to_nwb.zempolich_2024.
* `zempolich_2024_convert_session.py` : This conversion script defines the `session_to_nwb()` function, which converts a single session of data to NWB.
    When run as a script, this file converts 4 example sessions to NWB, representing all the various edge cases in the dataset.
* `zempolich_2024_convert_dataset.py` : This conversion script defines the `dataset_to_nwb()` function, which converts the entire Zempolich 2024 dataset to NWB.
    When run as a script, this file calls `dataset_to_nwb()` with the appropriate arguments.
* `zempolich_2024_nwbconverter.py` : This module defines the primary conversion class, `Zempolich2024NWBConverter`, which aggregates all of the various datainterfaces relevant for this conversion.
* `zempolich_2024_behaviorinterface.py` : This module defines `Zempolich2024BehaviorInterface`, which is the data interface for behavioral .mat files.
* `zempolich_2024_optogeneticinterface.py` : This module defines `Zempolich2024OptogeneticInterface`, which is the data interface for optogenetic stimulation from .mat files.
* `zempolich_2024_intrinsic_signal_imaging_interface.py` : This module defines `Zempolich2024IntrinsicSignalOpticalImagingInterface`, which is the data interface for intrinsic signal images (.tiff and .jpg).
* `zempolich_2024_open_ephys_recording_interface.py` : This module defines `Zempolich2024OpenEphysRecordingInterface`, which is a lightweight wrapper around neuroconv's `OpenEphysLegacyRecordingInterface` that is responsible for converting the OpenEphys recording data.
    This interface adds some extra conversion-specific metadata like relative channel positions, brain area, etc.
* `zempolich_2024metadata.yaml` : This metadata .yaml file provides high-level metadata for the nwb files directly as well as useful dictionaries for some of the data interfaces.
    For example,
    - Subject/species is "Mus musculus", which is directly included in the NWB file.
    - Ecephys/folder_name_to_start_datetime gives a mapping from 2-part folder names (ex. m53/Day1_A1) to session start times,
        which is used in cases where the session start time recorded by OpenEphys is ambiguous.

* `zempolich_2024_notes.md` : This markdown file contains my notes from the conversion for each of the data interfaces.
    It specifically highlights various edge cases as well as questions I had for the Schneider Lab (active and resolved).

Future conversions for this repo should follow the example of zempolich_2024 and create another folder of
conversion scripts and datainterfaces.  As a placeholder, here we have `src/schneider-lab-to-nwb/another_conversion`.

## Running a Conversion

To convert the 5 example sessions,
1. In `src/schneider_lab_to_nwb/zempolich_2024/zempolich_2024_convert_session.py`, update the `data_dir_path` and
    `output_dir_path` to appropriate local paths. `data_dir_path` should be the high-level directory where the data is
    stored, corresponding to `Grant Zempolich Project Data` in the GDrive. `output_dir_path` can be any valid path on
    your system where the output NWB files will be stored.
2. simply run
    ```bash
    python src/schneider_lab_to_nwb/zempolich_2024/zempolich_2024_convert_session.py
    ```
    Or, if running the conversion on a Windows machine, run
    ```bash
    python src\\schneider_lab_to_nwb\\zempolich_2024\\zempolich_2024_convert_session.py
    ```

To convert the whole dataset,
1. Update `data_dir_path` and `output_dir_path` in `src/schneider_lab_to_nwb/zempolich_2024/zempolich_2024_convert_all_sessions.py`
    as with the example sessions.
2. simply run
    ```bash
    python src/schneider_lab_to_nwb/zempolich_2024/zempolich_2024_convert_all_sessions.py
    ```
    Or, if running the conversion on a Windows machine, run
    ```bash
    python src\\schneider_lab_to_nwb\\zempolich_2024\\zempolich_2024_convert_all_sessions.py
    ```

Note that the dataset conversion uses multiprocessing, currently set to 4 workers.  To use more or fewer workers, simply
change the `max_workers` argument to `dataset_to_nwb()`.

## Uploading to DANDI

To upload the data to DANDI, follow the instructions [here](https://docs.dandiarchive.org/user-guide-sharing/uploading-data/), with the following changes:

* For step 5, instead of running the code as it appears in the instructions, use this
```bash
dandi download https://dandiarchive.org/dandiset/<dataset_id>/draft
cd <dataset_id>
dandi organize <source_folder> --update-external-file-paths --files-mode copy --media-files-mode copy
dandi validate .
dandi upload --sync
```
the extra options for dandi organize will ensure that the external movie files are organized and uploaded properly.
The --sync option removes extra external files on the dandi archive, which are renamed during the organize step.

## Contributing Your Changes

This section guides you through the process of extending the repository with your own custom changes and submitting them back to the main repository. Note that this process is temporary for syncing between the CatalystNeuro fork and the Schneider lab's fork until the official end of the conversion, after which the Schneider lab will maintain their own fork.

### Step 1: Create a GitHub account
1. Go to [https://github.com/](https://github.com/)
2. Sign up for a new account if you don't already have one

### Step 2: Fork the repository
1. Navigate to [https://github.com/catalystneuro/schneider-lab-to-nwb](https://github.com/catalystneuro/schneider-lab-to-nwb)
2. Click the "Fork" button in the top-right corner of the page
3. This creates a copy of the repository under your GitHub account

### Step 3: Clone your fork locally
```bash
git clone https://github.com/YOUR_USERNAME/schneider-lab-to-nwb
cd schneider-lab-to-nwb
```
Replace `YOUR_USERNAME` with your GitHub username.

### Step 4: Set up the development environment
```bash
conda env create --file make_env.yml
conda activate schneider_lab_to_nwb_env
```

### Step 5: Create a new branch for your changes
```bash
git checkout -b your-feature-name
```
Use a descriptive name for your branch that reflects the changes you're making.

### Step 6: Address TODOs
There are some placeholders in the current version of the conversion that will need to be filled in by the Schneider Lab
before the conversion can be completed with the full data/metadata. These placeholders are marked with TODOs in the code
to make them easier to spot, and a list is provided below for convenience:

* In `src/schneider_lab_to_nwb/zempolich_2024/zempolich_2024_open_ephys_recording_interface.py` Line 36,
    channel_positions are truncated to account for the 1-channel ephys data provided in the google drive. Lines 36-37
    will need to be removed to enable running the conversion on the full ephys data.
* In `src/schneider_lab_to_nwb/zempolich_2024/metadata.yaml` Line 29, the mapping between subject_id and genotype is a
    placeholder. Please specify the genotype for each subject, and it will automatically propagate to the NWB file.
* In `src/schneider_lab_to_nwb/zempolich_2024/metadata.yaml` Line 51, the mapping between subject_id and sex is a
    placeholder. Please specify the sex for each subject, and it will automatically propagate to the NWB file.

### Step 8: Commit your changes
```bash
git add .
git commit . -m "Brief description of your changes"
```

### Step 9: Push your changes to your fork
```bash
git push -u origin your-feature-name
```

### Step 10: Create a Pull Request
1. Go to your fork on GitHub at `https://github.com/YOUR_USERNAME/schneider-lab-to-nwb`
2. Click on "Pull request"
3. Click "New pull request"
4. Select your branch from the dropdown
5. Add a title and description explaining your changes
6. Click "Create pull request"
