"""Analytics data layer (Part 19). Metrics come ONLY from supplied files in
data/metrics/*.csv (columns: date, channel, asset_id, metric, value) or from a
connected integration. When there is nothing, callers must report NO DATA."""
from __future__ import annotations

import csv
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from aibos import paths

NO_DATA = "NO DATA"


@dataclass
class MetricRow:
    date: str
    channel: str
    asset_id: str
    metric: str
    value: float
    source_file: str


def load_metrics(directory: Path | None = None) -> list[MetricRow]:
    directory = Path(directory or paths.sub("metrics"))
    rows: list[MetricRow] = []
    for f in sorted(directory.glob("*.csv")):
        with f.open(newline="") as fh:
            for r in csv.DictReader(fh):
                try:
                    rows.append(MetricRow(r["date"].strip(), r.get("channel", "").strip().lower(),
                                          r.get("asset_id", "").strip(), r["metric"].strip().lower(),
                                          float(r["value"]), f.name))
                except (KeyError, ValueError, AttributeError, TypeError):
                    continue  # malformed rows are skipped, never guessed
    return rows


def filter_rows(rows: Iterable[MetricRow], metrics: list[str] | None = None,
                channels: list[str] | None = None) -> list[MetricRow]:
    out = list(rows)
    if metrics:
        out = [r for r in out if r.metric in metrics]
    if channels:
        out = [r for r in out if r.channel in channels]
    return out


def summarize(rows: list[MetricRow]) -> dict[str, dict[str, float]]:
    groups: dict[tuple[str, str], list[float]] = {}
    for r in rows:
        groups.setdefault((r.channel, r.metric), []).append(r.value)
    return {f"{c}/{m}": {"n": len(v), "sum": round(sum(v), 4), "mean": round(statistics.fmean(v), 4),
                         "min": min(v), "max": max(v)} for (c, m), v in sorted(groups.items())}


def series(rows: list[MetricRow]) -> dict[str, list[tuple[str, float]]]:
    out: dict[str, dict[str, float]] = {}
    for r in rows:
        out.setdefault(f"{r.channel}/{r.metric}", {}).setdefault(r.date, 0.0)
        out[f"{r.channel}/{r.metric}"][r.date] += r.value
    return {k: sorted(v.items()) for k, v in out.items()}


def robust_anomalies(points: list[tuple[str, float]], z_threshold: float = 3.0) -> list[dict]:
    vals = [v for _, v in points]
    if len(vals) < 5:
        return []
    med = statistics.median(vals)
    mad = statistics.median([abs(v - med) for v in vals]) or 1e-9
    out = []
    for d, v in points:
        z = 0.6745 * (v - med) / mad
        if abs(z) >= z_threshold:
            out.append({"date": d, "value": v, "robust_z": round(z, 2)})
    return out


def trend(points: list[tuple[str, float]]) -> dict[str, float] | None:
    if len(points) < 2:
        return None
    ys = [v for _, v in points]
    xs = list(range(len(ys)))
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (my + slope * (x - mx))) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return {"slope_per_period": round(slope, 4), "r2": round(r2, 3),
            "direction": "up" if slope > 0 else "down" if slope < 0 else "flat",
            "pct_change_first_to_last": round((ys[-1] - ys[0]) / ys[0] * 100, 2) if ys[0] else math.nan}
