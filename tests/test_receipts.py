import json
import threading
import time
from pathlib import Path

from understudy.receipts import atomic_write_json, read_json


def test_write_then_read_roundtrips(tmp_path):
    path = tmp_path / "runs" / "r1.json"
    atomic_write_json(path, {"a": 1, "b": [1, 2, 3]})
    assert read_json(path) == {"a": 1, "b": [1, 2, 3]}


def test_no_reader_ever_sees_a_partial_file(tmp_path):
    path = tmp_path / "r.json"
    atomic_write_json(path, {"version": 0})

    errors = []
    stop = threading.Event()

    def reader():
        while not stop.is_set():
            try:
                data = read_json(path)
                assert "version" in data  # never a truncated/invalid doc
            except json.JSONDecodeError as e:
                errors.append(e)

    t = threading.Thread(target=reader)
    t.start()
    for i in range(1, 50):
        atomic_write_json(path, {"version": i, "padding": "x" * 10_000})
    stop.set()
    t.join()
    assert not errors


def test_failed_write_does_not_leave_tmp_files(tmp_path):
    path = tmp_path / "r.json"

    class Unserializable:
        def __repr__(self):
            raise RuntimeError("boom")

    try:
        atomic_write_json(path, {"bad": Unserializable()})
    except Exception:
        pass
    leftovers = list(tmp_path.glob(".tmp-*"))
    assert leftovers == []
