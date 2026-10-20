import pytest

from model import Governance, Scenario, assess, rank_research, value_of_information


BASE = Scenario("abstract", 0.8, 0.4, 0.3, 0.25, 1.0, 0.35)


def test_assessment_is_reproducible():
    assert assess(BASE, seed=4) == assess(BASE, seed=4)


def test_governance_gate_reduces_priority():
    full = assess(BASE, Governance(), seed=2)
    weak = assess(BASE, Governance(public_registry=False, international_consultation=False), seed=2)
    assert weak.research_priority < full.research_priority


def test_non_reversible_work_is_not_ranked():
    result = assess(BASE, Governance(reversible_research_only=False))
    assert result.research_priority == 0


def test_more_precise_measurement_has_more_value():
    assert value_of_information(1, 0.2) > value_of_information(1, 0.8)


def test_bad_bounds_are_rejected():
    with pytest.raises(ValueError):
        assess(Scenario("bad", 1, 1.2, 0, 0, 1, 0))


def test_rank_research_orders_priority():
    candidates = [BASE, Scenario("known", 0.8, 0.4, 0.3, 0.25, 1, 0.9)]
    ranked = rank_research(candidates)
    assert ranked[0][1].research_priority >= ranked[1][1].research_priority
