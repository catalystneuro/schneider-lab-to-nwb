# Notes concerning the corredera_2025 conversion

## Stimulus
- Lots of relevant variables in the .mat files
- Based on the SfN poster, it looks like there are at least 4 different types of sessions:
    1. 60 min exploration on leaves/rubber (top left)
    2. exploration on VR environment (bottom left)
    3. 3-set session with self-generated playback (middle)
    4. exploration with Loom threat (right)
shared data looks like session type 1.
- Why are there 2 video files in example_data_ari_02?
- Skipped ISI bc it's fully recoverable from the stim times
- Skipped sound_id TTLs (sound data channel 2), bc sounds are already uniquely accounted for by index/name
- Skipped buffer_handle bc it's fully recoverable from stimulus template time series.


## Video

## Ephys
- brain region = left auditory cortex
- For channel positions, see CN_ASSY236_P1_kilosortChanMap.mat
- Recording Probe = 64-channel P1 probes from Cambridge Neurotech (ASSY-236)

## Sleap

## Audio
- Might want to switch to ndx-sound --> then add link for microphones and speakers
- .wav style compression?
- Are the microphones at different spots around the square arena? Which is where?


## Temporal Alignment
- Timestamps in the .mat file are relevant for temporal alignment
- Only the onset time of the ephys is recorded in the PTB (audio/video) clock -- no other ttls are recorded.

Data streams that need to be aligned:
- Video -- should have timestamps in the .mat file
- Audio Recording -- should have timestamps in the .mat file but also see align_audio_ephys.py
- Audio Stimulus -- should have timestamps in the .mat file
- SLEAP
- ephys
- spike sorting

Plan: Keep video/audio as the primary time basis and adjust ephys/sorting accordingly.

## Active Questions/Requests
