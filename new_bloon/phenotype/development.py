"""Genotype -> phenotype. Deterministic, pure, documented, bounded.
Implementasi dan dokumentasi memakai persamaan yang persis sama:
    s(A)=0, s(C)=1/3, s(G)=2/3, s(T)=1
    m       = 0.8 + 0.4 * GC(regulatory_region)
    trait_i = clamp01( m * weighted_locus_score_i )
    weighted_locus_score_i = sum_j (j+1)*s(locus_i[j]) / sum_j (j+1)
"""
from ..genome.layout import Genome, LOCUS_LEN
from ..genome.analysis import gc_content
from .traits import TRAIT_NAMES, clamp01

BASE_SCORE = {"A": 0.0, "C": 1.0 / 3.0, "G": 2.0 / 3.0, "T": 1.0}
_WEIGHT_DEN = sum(j + 1 for j in range(LOCUS_LEN))


def express(genome):
    """phenotype = F(genome); satu-satunya jalur genotype->phenotype."""
    m = 0.8 + 0.4 * gc_content(genome.regulatory_region())
    pheno = {}
    for i, trait in enumerate(TRAIT_NAMES):
        locus = genome.locus(i)
        raw = sum((j + 1) * BASE_SCORE[b]
                  for j, b in enumerate(locus)) / _WEIGHT_DEN
        pheno[trait] = clamp01(m * raw)
    return pheno