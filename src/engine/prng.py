"""Deterministic randomness: every frame depends only on (seed, t).

The same (seed, t) always yields the same sequence, so two renders with the
same parameters are byte-identical (checked by tools/verify.py).
"""
import random


def prng(seed, t):
    """A random.Random for one frame: state = f(seed, quantised song time)."""
    return random.Random(f"{seed}:{round(t * 1000)}")
