"""Candidate = phenotype vector yang ditawarkan ke system under test."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    individual_id: str
    phenotype: dict

    def to_dict(self):
        return {"individual_id": self.individual_id,
                "phenotype": dict(self.phenotype)}