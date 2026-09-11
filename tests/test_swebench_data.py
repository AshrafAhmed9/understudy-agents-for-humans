"""Proves the cached real dataset loads correctly and the patch/answer key
never leaks into the agent-facing Instance type."""

from understudy.data.swebench import DEFAULT_CACHE_PATH, epoch_image_ref, load_cases


def test_cache_file_exists():
    assert DEFAULT_CACHE_PATH.exists(), "run the fetch step before testing this"


def test_loads_at_least_one_case():
    cases = load_cases()
    assert len(cases) >= 1


def test_instance_field_set_excludes_any_patch(monkeypatch=None):
    # Not just "we didn't populate it" — Instance has no patch-shaped field
    # at all, so this is a type-level guarantee, checked here for real.
    cases = load_cases()
    for case in cases:
        assert not hasattr(case.instance, "gold_patch")
        assert not hasattr(case.instance, "patch")
        assert "gold_patch" not in type(case.instance).model_fields
        assert "patch" not in type(case.instance).model_fields


def test_scoring_case_carries_the_gold_patch():
    cases = load_cases()
    assert all(case.gold_patch for case in cases)


def test_instance_ids_are_unique():
    cases = load_cases()
    ids = [c.instance.instance_id for c in cases]
    assert len(ids) == len(set(ids))


def test_real_issue_text_is_substantive():
    cases = load_cases()
    # Sanity check this is real problem-statement text, not a placeholder.
    assert all(len(c.instance.issue_text) > 50 for c in cases)


def test_epoch_image_ref_format():
    ref = epoch_image_ref("astropy__astropy-12907")
    assert ref == "ghcr.io/epoch-research/swe-bench.eval.x86_64.astropy__astropy-12907"
