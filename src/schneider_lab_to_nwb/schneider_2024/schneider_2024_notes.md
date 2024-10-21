# Notes concerning the schneider_2024 conversion

## Behavior

## Video

## Optogenetics
- is_opto_trial in the trials table is `np.logical_not(np.isnan(onset_times))` rather than reading from the .mat file
    to ensure consistency with the onset/offset times.

## Data Requests
- Mice sexes
- Remaining data for Grant's project
- More detailed position info for recording probe
- Detailed description of temporal alignment procedure.
