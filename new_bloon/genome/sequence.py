"""Nucleotide-style sequence validation for synthetic computational genomes.
Perilaku terdokumentasi: input di-upper-case; lowercase {a,c,g,t} diterima
dan dinormalisasi menjadi uppercase.
"""
VALID_BASES = frozenset("ACGT")


class SequenceError(ValueError):
    """Raised for malformed sequences."""


def validate(seq, expected_length=None):
    """Return seq.upper(); raise SequenceError on any malformed input."""
    if not isinstance(seq, str):
        raise SequenceError("sequence must be str, got " + type(seq).__name__)
    if len(seq) == 0:
        raise SequenceError("empty sequence")
    bad = sorted(set(c for c in seq.upper() if c not in VALID_BASES))
    if bad:
        raise SequenceError("invalid bases: " + repr(bad))
    if expected_length is not None and len(seq) != expected_length:
        raise SequenceError("incorrect genome length: {} != {}".format(
            len(seq), expected_length))
    return seq.upper()