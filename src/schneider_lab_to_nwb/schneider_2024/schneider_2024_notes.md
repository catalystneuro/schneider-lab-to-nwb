# Notes concerning the schneider_2024 conversion

## Behavior

## Video

## Optogenetics
- is_opto_trial in the trials table is `np.logical_not(np.isnan(onset_times))` rather than reading from the .mat file
    to ensure consistency with the onset/offset times.

## Intrinsic Signal Optical Imaging
- Just including raw blood vessel image and processed overlay + pixel locations bc including the isoi roi response series would really require an extension for context, but seems like it has limited reuse potential.
- Used the Audette paper for description of overlay image.
- Need pixel locs for ephys
- Need device info for 2p microscope and red light laser
- Why is the overlaid image flipped left/right compared to the original?


## Data Requests
- Mice sexes
- Remaining data for Grant's project
- More detailed position info for recording probe
- Detailed description of temporal alignment procedure.
