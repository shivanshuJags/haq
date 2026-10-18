from core import verdict as V
from core.catalog import Scheme
from core.candidates import Candidate
from core.eligibility import Assessment
from core.profile import Profile
from core.rules import EligibilityRules


def make_candidate(scheme_id: str) -> Candidate:
    scheme = Scheme(id=scheme_id, country="UK", regions=None, name="Test", summary=None, categories=[],
                    sections={}, apply_url=None, source_url="https://example.org", source=None, meta={},
                    rules=EligibilityRules())
    return Candidate(scheme, 0.5, Assessment([]))


def test_same_input_is_answered_once(monkeypatch):
    calls = []

    def fake_judge(candidate, profile, country, language):
        calls.append(candidate.scheme.id)
        return V.Verdict(verdict="likely_eligible", fit="strong", reasons=[], benefit="£1",
                         yearly_amount=1, to_confirm=[], next_step=None)

    monkeypatch.setattr(V, "_judge", fake_judge)
    V._cache.clear()
    candidate, profile = make_candidate("uk:test"), Profile(age=31)

    first = V.judge(candidate, profile, "UK", "english")
    second = V.judge(candidate, profile, "UK", "english")
    assert first is second          # identical answer
    assert calls == ["uk:test"]     # the model was asked only once

    V.judge(candidate, Profile(age=32), "UK", "english")  # different person -> asked again
    assert len(calls) == 2


def test_failures_are_not_cached(monkeypatch):
    monkeypatch.setattr(V, "_judge", lambda *args: None)
    V._cache.clear()
    assert V.judge(make_candidate("uk:fail"), Profile(), "UK", "english") is None
    assert len(V._cache) == 0
