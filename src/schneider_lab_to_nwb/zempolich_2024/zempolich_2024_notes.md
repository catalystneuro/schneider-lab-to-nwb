# Notes concerning the schneider_2024 conversion

## Behavior

## Video
- M2EphysVideos/m80/240819 is missing video for Cam2

## Optogenetics
- is_opto_trial in the trials table is `np.logical_not(np.isnan(onset_times))` rather than reading from the .mat file
    to ensure consistency with the onset/offset times.

## Intrinsic Signal Optical Imaging
- Just including raw blood vessel image and processed overlay + pixel locations bc including the isoi roi response series would really require an extension for context, but seems like it has limited reuse potential.
- Used the Audette paper for description of overlay image.

## Temporal Alignment
- For session A1/m53/Day1 (raw_m53_231029_001.mat),
    - ephys data starts at 1025s with duration 2700s
    - units table runs from 0-2700
    - behavioral time series (lick and encoder) run from 1187s to 2017s
    - events table (toneIN, toneOUT, targetOUT, valve) run from 1191s to 1954s
    - valued events table () runs from 2017 to 2164
    - trials table () runs from 1191 to 1993
    --> conclusion: something is wrong with ephys start time --> ignoring it
- Splitting data into epochs: Active Behavior and Passive Listening
- Looks like opto sessions are not temporally aligned (no concurrent ephys and timestamp start at large numbers (142697.1119976)) --> normalizing those sessions times to first encoder timestamp.
