"""CUES: every time in the film that is NOT on the beat grid, in ONE place.

  name: [seconds (song time), source, note]
  source 'measured' = measured from the audio (or taken from the verified
  word_timeline.json alignment, which is measured data); 'initial' = the value
  the task book gave, not yet re-measured - check these by ear first.

TO CORRECT A CUE: change the number here and nowhere else.
"""

CUES = {
    # --- ending (S15/S16) ---
    "l97_onset":   [205.37, "measured", "final lyric line word onset (word_timeline.json)"],
    "l97_syl2":    [205.96, "initial",  "second syllable of the final word (check by ear)"],
    "l97_syl3":    [206.19, "initial",  "third syllable (check by ear)"],
    "l97_syl4":    [206.42, "initial",  "fourth syllable (check by ear)"],
    "silence_at":  [207.08, "measured", "the song stops dead (RMS falls to the floor)"],
    "chime":       [207.873, "measured", "heart lights up: the film's only sound design point"],
    "end":         [211.9, "measured",  "film length (song file duration)"],
    # --- S10 first red (v4: locked to L64) ---
    "first_red":   [131.21, "measured", "illegal arguments word onset (word_timeline.json)"],
    # --- S12 last shout (the only frames she appears) ---
    "last_syl1":   [161.88, "initial",  "the four blocks of the last shout (check by ear)"],
    "last_syl2":   [162.11, "initial",  ""],
    "last_syl3":   [162.34, "initial",  ""],
    "last_syl4":   [162.57, "initial",  ""],
    # --- S14 frame that must hold still ≥1.2s ---
    "heart_close": [192.3, "initial",   "heart curve closes; brightest frame (check by ear)"],
    # --- S16 ending line ---
    "exit_line":   [210.0, "initial",   "execution complete log line (check by ear)"],
    # --- S15 -> S16 transition: the single white flash, beat-locked ---
    "s16_flash":   [209.87, "initial",  "1-frame white flash before the black field"],
}


def cue(name: str) -> float:
    if name not in CUES:
        raise KeyError(f"cues.py: no cue named {name!r}")
    return CUES[name][0]
