"""Analytics rules (Part 19). Only supplied data; NO DATA otherwise."""
from __future__ import annotations

from pathlib import Path

from aibos import analytics, config, integrations, paths
from aibos.experiments import ExperimentStore, evaluate_ab
from aibos.rules import out, rule
from aibos.schemas import RunStatus

CHANNEL_INTEGRATION = {"x": "x_api", "linkedin": "linkedin_api", "instagram": "instagram_api",
                       "tiktok": "tiktok_api", "youtube": "youtube_api", "facebook": "facebook_api",
                       "reddit": "reddit_api", "newsletter": "email_provider", "email": "email_provider",
                       "website": "web_analytics", "blog": "web_analytics"}


def _rows(ctx):
    rows = ctx.board.get("_metrics")
    if rows is None:
        rows = analytics.load_metrics()
        ctx.board["_metrics"] = rows
    return rows


def _no_data(spec, ctx, what: str):
    return out(spec, ctx, status=RunStatus.DEGRADED,
               findings=[f"NO DATA: {what}. No metrics were fabricated."],
               uncertainties=["performance unknown until data is supplied"],
               next_action="export analytics to data/metrics/*.csv (date,channel,asset_id,metric,value) "
                           "or connect an analytics integration",
               data={"analytics": [{"agent_id": spec.agent_id, "status": analytics.NO_DATA}]})


@rule("metrics")
def metrics(ctx, spec):
    rows = analytics.filter_rows(_rows(ctx), spec.params.get("metrics"), spec.params.get("channels"))
    if not rows:
        return _no_data(spec, ctx, f"no rows for metrics={spec.params.get('metrics', 'any')} channels={spec.params.get('channels', 'any')}")
    summary = analytics.summarize(rows)
    return out(spec, ctx, findings=[f"{k}: n={v['n']} sum={v['sum']} mean={v['mean']}" for k, v in summary.items()],
               data={"analytics": [{"agent_id": spec.agent_id, "summary": summary}]},
               sources=sorted({r.source_file for r in rows}), confidence=0.9)


@rule("anomaly")
def anomaly(ctx, spec):
    rows = _rows(ctx)
    if not rows:
        return _no_data(spec, ctx, "no metric rows")
    z = float(spec.params.get("z_threshold", 3.0))
    found = {k: a for k, pts in analytics.series(rows).items() if (a := analytics.robust_anomalies(pts, z))}
    return out(spec, ctx, findings=[f"{k}: {v}" for k, v in found.items()] or ["no anomalies"],
               data={"analytics": [{"agent_id": spec.agent_id, "anomalies": found}]}, confidence=0.8)


@rule("trend")
def trend(ctx, spec):
    rows = _rows(ctx)
    if not rows:
        return _no_data(spec, ctx, "no metric rows")
    mn = int(spec.params.get("min_points", 4))
    trends = {k: t for k, pts in analytics.series(rows).items() if len(pts) >= mn and (t := analytics.trend(pts))}
    return out(spec, ctx, findings=[f"{k}: {t['direction']} (slope {t['slope_per_period']}, r2 {t['r2']})" for k, t in trends.items()] or ["not enough points for trends"],
               data={"analytics": [{"agent_id": spec.agent_id, "trends": trends}]}, confidence=0.7)


@rule("funnel")
def funnel(ctx, spec):
    steps = spec.params.get("steps", ["impressions", "clicks", "signups", "purchases"])
    rows = _rows(ctx)
    totals = {s: sum(r.value for r in rows if r.metric == s) for s in steps}
    if not any(totals.values()):
        return _no_data(spec, ctx, f"no funnel metrics {steps}")
    conv = {f"{a}->{b}": round(totals[b] / totals[a], 4) if totals[a] else None for a, b in zip(steps, steps[1:])}
    return out(spec, ctx, findings=[f"{k}: {v}" for k, v in conv.items()],
               data={"analytics": [{"agent_id": spec.agent_id, "funnel": totals, "conversion": conv}]}, confidence=0.8)


@rule("unit_economics")
def unit_economics(ctx, spec):
    rows = _rows(ctx)
    tot = lambda m: sum(r.value for r in rows if r.metric == m)  # noqa: E731
    spend, new_c, revenue, customers = tot("spend"), tot("new_customers"), tot("revenue"), tot("customers")
    if not (spend or revenue):
        return _no_data(spec, ctx, "no spend/revenue/new_customers rows")
    res = {"spend": spend, "new_customers": new_c, "revenue": revenue,
           "CAC": round(spend / new_c, 2) if new_c else None,
           "ARPU": round(revenue / customers, 2) if customers else None}
    return out(spec, ctx, findings=[f"{k}: {v}" for k, v in res.items()],
               data={"analytics": [{"agent_id": spec.agent_id, "unit_economics": res}]}, confidence=0.8,
               uncertainties=["LTV requires retention data over time"] if res["ARPU"] else [])


@rule("cohort")
def cohort(ctx, spec):
    rows = [r for r in _rows(ctx) if r.metric.startswith("cohort_")]
    if not rows:
        return _no_data(spec, ctx, "no cohort_* metrics")
    table: dict[str, dict[str, float]] = {}
    for r in rows:
        table.setdefault(r.asset_id, {})[r.metric] = r.value
    return out(spec, ctx, findings=[f"{len(table)} cohorts"], data={"analytics": [{"agent_id": spec.agent_id, "cohorts": table}]}, confidence=0.8)


@rule("attribution")
def attribution(ctx, spec):
    rows = [r for r in _rows(ctx) if r.metric in ("conversions", "signups", "purchases")]
    if not rows:
        return _no_data(spec, ctx, "no conversion rows by channel")
    by = {}
    for r in rows:
        by[r.channel] = by.get(r.channel, 0) + r.value
    total = sum(by.values())
    share = {k: round(v / total, 3) for k, v in by.items()} if total else {}
    return out(spec, ctx, findings=[f"{k}: {v:.0%}" for k, v in share.items()],
               uncertainties=["channel-reported conversions (last-touch); not causal attribution"],
               data={"analytics": [{"agent_id": spec.agent_id, "attribution_share": share}]}, confidence=0.5)


@rule("experiment_analysis")
def experiment_analysis(ctx, spec):
    exps = list(ctx.board.get("experiments", []) or []) + ExperimentStore().all()
    if not exps:
        return _no_data(spec, ctx, "no experiments registered")
    results = []
    for e in exps:
        d = e.get("data", {}) or {}
        if all(k in d for k in ("conv_a", "n_a", "conv_b", "n_b")):
            results.append({"experiment": e.get("name"), **evaluate_ab(d["conv_a"], d["n_a"], d["conv_b"], d["n_b"])})
        else:
            results.append({"experiment": e.get("name"), "status": "NOT RUN — no results supplied"})
    return out(spec, ctx, findings=[f"{r['experiment']}: {r.get('interpretation', r.get('status'))}" for r in results],
               data={"analytics": [{"agent_id": spec.agent_id, "experiments": results}]}, confidence=0.9)


@rule("feedback_summary")
def feedback_summary(ctx, spec):
    d = paths.sub("feedback")
    files = sorted(p for p in d.glob("*") if p.suffix in (".txt", ".md", ".csv"))
    if not files:
        return _no_data(spec, ctx, "no feedback files in data/feedback/")
    from collections import Counter
    from aibos.rules import content_words
    words = Counter()
    n_items = 0
    for f in files:
        lines = [l for l in Path(f).read_text().splitlines() if l.strip()]
        n_items += len(lines)
        for l in lines:
            words.update(content_words(l))
    themes = [w for w, _ in words.most_common(15)]
    return out(spec, ctx, findings=[f"{n_items} feedback items from {len(files)} files", f"frequent terms: {themes}"],
               data={"audience_insights": [{"insight": f"frequent feedback terms: {themes}", "status": "OBSERVED",
                                            "evidence": [f.name for f in files], "how_to_validate": "read the items"}]},
               confidence=0.6)


@rule("analytics_plan")
def analytics_plan(ctx, spec):
    plats = config.platforms()
    plan = {"content_metrics": [], "experiment_metrics": [], "integrations_needed": {}, "data_import": "data/metrics/*.csv"}
    for a in ctx.board.get("content", []) or []:
        p = a.get("platform", "")
        integ = plats.get(p, {}).get("integration")
        metrics = (["opens", "open_rate", "clicks", "unsubscribes"] if p == "newsletter"
                   else ["impressions", "engagement_rate", "profile_visits", "link_clicks"])
        plan["content_metrics"].append({"artifact_id": a.get("artifact_id"), "platform": p, "metrics": metrics,
                                        "integration": integ,
                                        "integration_status": integrations.status(integ).status if integ else "N/A"})
        if integ:
            plan["integrations_needed"][integ] = integrations.status(integ).status
    for e in ctx.board.get("experiments", []) or []:
        plan["experiment_metrics"].append({"experiment": e.get("name"), "metric": e.get("metric"),
                                           "success": e.get("success_criteria"), "failure": e.get("failure_criteria")})
    missing = [k for k, v in plan["integrations_needed"].items() if v != integrations.CONNECTED]
    return out(spec, ctx, findings=[f"{len(plan['content_metrics'])} content items and {len(plan['experiment_metrics'])} experiments to measure"],
               uncertainties=[f"{m}: NOT CONNECTED — results must be exported manually to data/metrics/" for m in missing],
               data={"analytics_plan": plan}, confidence=1.0,
               next_action="after publishing (with approval), export metrics weekly and run `aibos analytics`")
