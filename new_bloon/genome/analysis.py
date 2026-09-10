"""Sequence-level computation (bioinformatics-inspired) pada genome sintetis."""


def gc_content(seq):
    if not seq:
        return 0.0
    return (seq.count("G") + seq.count("C")) / len(seq)


def hamming_distance(a, b):
    if len(a) != len(b):
        raise ValueError("hamming requires equal lengths")
    return sum(1 for x, y in zip(a, b) if x != y)


def genetic_distance(a, b):
    """Normalized Hamming distance in [0,1]."""
    return hamming_distance(a, b) / len(a)


def edit_distance(a, b):
    """Levenshtein distance (perbandingan indel-aware / analisis diversity)."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (1 if ca != cb else 0)))
        prev = cur
    return prev[-1]