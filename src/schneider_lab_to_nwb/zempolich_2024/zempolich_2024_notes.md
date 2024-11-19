# Notes concerning the schneider_2024 conversion

## Behavior

## Video

## Optogenetics
- is_opto_trial in the trials table is `np.logical_not(np.isnan(onset_times))` rather than reading from the .mat file
    to ensure consistency with the onset/offset times.
- injection vs stimulation location(s) for A1 vs M2???

## Intrinsic Signal Optical Imaging
- Just including raw blood vessel image and processed overlay + pixel locations bc including the isoi roi response series would really require an extension for context, but seems like it has limited reuse potential.
- Used the Audette paper for description of overlay image.
- Need pixel locs for ephys
- Need device info for 2p microscope and red light laser
- Why is the overlaid image flipped left/right compared to the original?

# Temporal Alignment
- For session A1/m53/Day1 (raw_m53_231029_001.mat),
    - ephys data starts at 1025s with duration 2700s
    - units table runs from 0-2700
    - behavioral time series (lick and encoder) run from 1187s to 2017s
    - events table (toneIN, toneOUT, targetOUT, valve) run from 1191s to 1954s
    - valued events table () runs from 2017 to 2164
    - trials table () runs from 1191 to 1993
    --> conclusion: something is wrong with ephys start time
- Want to split data into epochs: Active Behavior, Passive Listening, ??? What is happening post-2164? Before 1187s?
- For opto sessions, what is the session start time? Ex. What is file['metadata']['session_beginning'] (=129765.7728241)?
- Looks like opto sessions are not temporally aligned (no concurrent ephys and timestamp start at large numbers (142697.1119976))



## Data Requests
- Mice sexes
- Remaining data for Grant's project
- More detailed position info for recording probe
- Detailed description of temporal alignment procedure.
