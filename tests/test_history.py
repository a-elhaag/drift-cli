import json

from drift_cli.core.history import HistoryManager


def test_add_and_get_history_order(tmp_path, make_plan):
    history = HistoryManager(drift_dir=tmp_path / "drift")

    history.add_entry("first", make_plan(command="echo first"), executed=False)
    history.add_entry("second", make_plan(command="echo second"), executed=True)

    entries = history.get_history(limit=2)
    assert [entry.query for entry in entries] == ["second", "first"]


def test_create_snapshot_and_restore(fake_home):
    drift_dir = fake_home / ".drift"
    history = HistoryManager(drift_dir=drift_dir)

    source_file = fake_home / "project" / "demo.txt"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("before")

    snapshot_id = history.create_snapshot([str(source_file)])

    metadata_path = history.snapshots_dir / snapshot_id / "metadata.json"
    metadata = json.loads(metadata_path.read_text())
    assert metadata["id"] == snapshot_id
    assert len(metadata["files"]) == 1

    source_file.write_text("after")
    assert history.restore_snapshot(snapshot_id) is True
    assert source_file.read_text() == "before"


def test_restore_snapshot_rejects_unsafe_identifier(tmp_path):
    history = HistoryManager(drift_dir=tmp_path / "drift")
    assert history.restore_snapshot("../evil") is False
    assert history.restore_snapshot(".hidden") is False
    assert history.restore_snapshot("") is False
