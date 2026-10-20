"""Decision analysis for stratospheric-aerosol research portfolios.

This module compares abstract climate-response hypotheses and governance gates.
It intentionally omits delivery systems, quantities, locations, and operations.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import math
import random


@dataclass(frozen=True)
class Scenario:
    name: str
    radiative_response: float
    ozone_risk: float
    stratospheric_heating: float
    precipitation_shift: float
    persistence_years: float
    evidence_quality: float


@dataclass(frozen=True)
class Governance:
    independent_review: bool = True
    public_registry: bool = True
    international_consultation: bool = True
    reversible_research_only: bool = True

    @property
    def gate_score(self) -> float:
        return sum(asdict(self).values()) / 4


@dataclass(frozen=True)
class Assessment:
    expected_knowledge_gain: float
    tail_risk: float
    regional_inequality: float
    termination_risk: float
    governance_score: float
    research_priority: float


def _validate(s: Scenario) -> None:
    values = (s.ozone_risk, s.stratospheric_heating, s.precipitation_shift,
              s.evidence_quality)
    if any(not 0 <= x <= 1 for x in values) or s.persistence_years <= 0:
        raise ValueError("risk and evidence inputs must be bounded; persistence positive")


def assess(s: Scenario, governance: Governance = Governance(), draws: int = 2000,
           seed: int = 11) -> Assessment:
    _validate(s)
    if draws < 100:
        raise ValueError("use at least 100 uncertainty draws")
    rng = random.Random(seed)
    risks, inequality, termination, gains = [], [], [], []
    for _ in range(draws):
        sensitivity = max(0.2, rng.lognormvariate(0, 0.28))
        coupling = min(1.5, max(0.2, rng.gauss(1, 0.18)))
        response = abs(s.radiative_response) * sensitivity
        ozone = s.ozone_risk * coupling
        heating = s.stratospheric_heating * sensitivity
        precip = s.precipitation_shift * coupling
        risks.append(max(ozone, heating, precip))
        inequality.append(precip * (0.7 + 0.6 * rng.random()))
        termination.append(response * math.sqrt(s.persistence_years) * 0.12)
        gains.append((1 - s.evidence_quality) * response / (1 + ozone + heating))
    risks.sort()
    tail = risks[int(0.95 * draws)]
    mean = lambda xs: sum(xs) / len(xs)
    gain = mean(gains)
    gate = governance.gate_score
    priority = gate * gain / (1 + tail + mean(inequality) + mean(termination))
    if not governance.reversible_research_only:
        priority = 0.0
    return Assessment(gain, tail, mean(inequality), mean(termination), gate, priority)


def value_of_information(base_uncertainty: float, measurement_precision: float,
                         decision_stakes: float = 1.0) -> float:
    """Bounded proxy for uncertainty reduction from a proposed observation."""
    if min(base_uncertainty, measurement_precision, decision_stakes) < 0:
        raise ValueError("inputs must be non-negative")
    if base_uncertainty == 0:
        return 0.0
    posterior = 1 / (1 / base_uncertainty ** 2 + 1 / max(1e-9, measurement_precision) ** 2)
    reduction = base_uncertainty ** 2 - posterior
    return decision_stakes * reduction / (1 + reduction)


def rank_research(scenarios: list[Scenario], governance: Governance = Governance(),
                  seed: int = 11) -> list[tuple[Scenario, Assessment]]:
    ranked = [(s, assess(s, governance, seed=seed + i)) for i, s in enumerate(scenarios)]
    return sorted(ranked, key=lambda pair: pair[1].research_priority, reverse=True)


if __name__ == "__main__":
    abstract = Scenario("abstract sulfate-like hypothesis", 0.8, 0.45, 0.4, 0.35, 1.2, 0.3)
    print(json.dumps(asdict(assess(abstract)), indent=2))
