"""kvwire export: build, validate, write. Fixtures are synthetic (tests/fixtures/export)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from kvwire.cli import main
from kvwire.export import build, has_errors, validate
from kvwire.export.build import env_hash, percentile
from kvwire.export.rows import COLUMN_UNITS
from kvwire.export.write import push, render_card, write_dataset

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "export"
GDR, RXE = FIX / "run_gdr", FIX / "run_rxe"


def test_percentile_nearest_rank() -> None:
    assert percentile([5, 1, 3, 2, 4], 50) == 3
    assert percentile([5, 1, 3, 2, 4], 99) == 5
    assert percentile([7.0], 99) == 7.0


def test_env_hash_is_stable_and_order_independent() -> None:
    a = json.loads((GDR / "manifest.json").read_text())
    b = dict(reversed(list(a.items())))
    assert env_hash(a) == env_hash(b)
    assert env_hash(a) != env_hash({**a, "nic_fw": "9.9"})


def test_build_aggregates_and_normalises_against_both_ceilings() -> None:
    ds = build([GDR])
    assert {t.key.kv_layout for t in ds.transfers} == {"interleaved", "separate"}
    t = next(t for t in ds.transfers if t.key.kv_layout == "interleaved")
    assert t.n_reps == 5
    assert t.duration_ns_p50 == 520_000
    assert t.throughput_gb_per_s == pytest.approx(4_000_000 / 520_000)
    assert t.ceiling_region_gb_per_s == 10.0  # same 64 KiB message size
    assert t.ceiling_peak_gb_per_s == 12.0  # large-message plateau
    assert t.efficiency_vs_region_ceiling == pytest.approx(t.throughput_gb_per_s / 10.0)
    assert t.efficiency_vs_peak == pytest.approx(t.throughput_gb_per_s / 12.0)
    assert t.cpu_s_per_gb == pytest.approx(100_000 / 4_000_000)
    s = next(t for t in ds.transfers if t.key.kv_layout == "separate")
    assert s.ceiling_region_gb_per_s == 8.0
    assert s.cpu_s_per_gb is None  # not measured
    assert not t.host_staging
    assert ds.prefill[0].n_reps == 3
    assert ds.prefill[0].duration_ms_p50 == 110.0


def test_layer_timelines_join_events_with_prefill_windows() -> None:
    rows = build([GDR]).layer_timelines
    assert [(r.layer, r.send_after_compute_ns, r.commit_ns) for r in rows] == [
        (0, 500, None),
        (1, 600, 3700),  # commit lands on the last layer's row
    ]


def test_rxe_runs_never_enter_main_configs() -> None:
    ds = build([GDR, RXE])
    assert ds.dropped_rxe_rows == 6
    rxe_hash = next(e.env_hash for e in ds.environments if e.is_rxe)
    for name, rows in ds.configs().items():
        if name != "environments":
            assert all(r.env_hash != rxe_hash for r in rows), name
    assert not has_errors(validate(ds))


def test_clean_fixture_passes_validation() -> None:
    assert validate(build([GDR])) == []


def test_missing_ceiling_and_bad_joins_are_errors(tmp_path: Path) -> None:
    run = tmp_path / "run_gdr"
    shutil.copytree(GDR, run)
    (run / "ceiling" / "ceilings.csv").write_text(
        "nic,message_bytes,n_qps,memory,bw_gb_per_s,lat_us\nnic0,65536,1,gpu,10.0,6.0\n"
    )
    ds = build([run])
    issues = validate(ds)
    assert any(i.check == "ceiling coverage" and "32768" in i.message for i in issues)
    ds.run_ids.discard("run_gdr")
    assert any(i.check == "joinability" for i in validate(ds))
    assert has_errors(validate(ds))


def test_efficiency_above_one_is_flagged(tmp_path: Path) -> None:
    run = tmp_path / "run_gdr"
    shutil.copytree(GDR, run)
    (run / "ceiling" / "ceilings.csv").write_text(
        "nic,message_bytes,n_qps,memory,bw_gb_per_s,lat_us\n"
        "nic0,65536,1,gpu,1.0,\nnic0,32768,1,gpu,8.0,\n"
    )
    issues = validate(build([run]))
    flagged = [i for i in issues if i.check == "physical sanity"]
    assert flagged
    assert all(i.level == "warning" for i in flagged)


def test_every_numeric_column_has_a_unit() -> None:
    assert not [i for i in validate(build([GDR])) if i.check == "units"]
    assert COLUMN_UNITS["throughput_gb_per_s"].startswith("GB/s")


def test_write_jsonl_and_card(tmp_path: Path) -> None:
    ds = build([GDR, RXE])
    paths = write_dataset(ds, tmp_path, "jsonl")
    names = {p.parent.name for p in paths if p.suffix == ".jsonl"}
    assert names == {
        "transfers",
        "transfers_raw",
        "layer_timelines",
        "ceilings",
        "prefill",
        "environments",
    }
    first = json.loads((tmp_path / "transfers" / "transfers.jsonl").read_text().splitlines()[0])
    assert "message_bytes" in first
    assert "key" not in first
    card = (tmp_path / "README.md").read_text()
    assert "license: cc-by-4.0" in card
    assert "{{" not in card
    assert "config_name: layer_timelines" in card
    assert "fixture-nic" in card


def test_card_lists_only_present_configs() -> None:
    ds = build([GDR])
    ds.layer_timelines.clear()
    assert "config_name: layer_timelines" not in render_card(ds, "parquet", "abc")


def test_parquet_roundtrip(tmp_path: Path) -> None:
    pq = pytest.importorskip("pyarrow.parquet")
    write_dataset(build([GDR]), tmp_path, "parquet")
    assert pq.read_table(tmp_path / "ceilings" / "ceilings.parquet").num_rows == 3


def test_push_requires_typed_confirmation(tmp_path: Path) -> None:
    assert push(tmp_path, "someone/some-repo", confirm=lambda _: "no") is False


def test_cli_validate_only_and_failure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["export", "--runs", str(GDR), "--validate-only"]) == 0
    run = tmp_path / "run_gdr"
    shutil.copytree(GDR, run)
    (run / "ceiling" / "ceilings.csv").unlink()
    assert (
        main(["export", "--runs", str(run), "--out", str(tmp_path / "o"), "--format", "jsonl"]) == 1
    )
    assert not (tmp_path / "o").exists()
    assert "nothing written" in capsys.readouterr().err
