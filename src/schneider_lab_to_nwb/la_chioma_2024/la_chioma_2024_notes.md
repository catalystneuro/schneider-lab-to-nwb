# Notes concerning the la_chioma_2024 conversion

## Recording

- Ephys data in Open Ephys binary format (continuous.dat)
- AP stream ("Neuropix-PXI-100.ProbeA")
- NIDAQ stream ("NI-DAQmx-107.PXIe-6341")

### Issues

- The settings file (`AL240404c_2024-04-22_17-45-19/Record Node 102/settings.xml`) was missing channel definitions for channels `364` and `365`.
  This caused downstream tools to fail when parsing the file.

### Fixing missing channels in Open Ephys XML

To address this issue, we developed a script (`fix_openephys_xml_missing_channels.py`) that automatically detects and fills in missing channel definitions in the Open Ephys XML settings file. The script infers the missing values based on existing patterns in the file, ensuring compatibility with downstream processing tools.

**Note:** This step must be performed before running the NWB conversion to ensure that all channel information is present and correct.

To fix the XML file, run the following command:

```bash
  python fix_openephys_xml_missing_channels.py --file_path settings.xml --verbose
```
