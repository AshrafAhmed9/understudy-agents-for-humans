import pytest

from understudy.tools.repo_access import read_file, search_source


@pytest.fixture()
def repo(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("def f():\n    raise ValueError('boom')\n")
    (tmp_path / "pkg" / "b.py").write_text("def g():\n    return 42\n")
    return tmp_path


def test_read_file_returns_contents(repo):
    assert "raise ValueError" in read_file(repo, "pkg/a.py")


def test_read_file_blocks_traversal(repo):
    with pytest.raises(PermissionError):
        read_file(repo, "../../etc/passwd")


def test_read_file_truncates_large_files(repo):
    big = repo / "big.py"
    big.write_text("x = 1\n" * 20_000)
    text = read_file(repo, "big.py")
    assert "truncated" in text


def test_search_source_finds_matches(repo):
    hits = search_source(repo, r"raise ValueError")
    assert len(hits) == 1
    assert hits[0]["path"] == "pkg/a.py"


def test_search_source_rejects_bad_regex(repo):
    with pytest.raises(ValueError):
        search_source(repo, r"(unclosed")


def test_search_source_caps_results(repo):
    many = repo / "many.py"
    many.write_text("TODO\n" * 500)
    hits = search_source(repo, "TODO", glob="many.py")
    from understudy.tools.repo_access import MAX_MATCHES
    assert len(hits) == MAX_MATCHES
