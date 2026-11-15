from prometheus_client import Gauge
from . import config, cost_data
 
COST_LATEST = Gauge("aws_cost_latest_day_usd", "Total AWS cost for the latest full day")
COST_BASELINE = Gauge("aws_cost_baseline_usd", "Configured daily cost baseline")
COST_SERVICE = Gauge("aws_cost_service_usd", "Latest-day cost per service", ["service"])
 
 
def refresh():
    rows = cost_data.daily_cost_by_service()
    COST_BASELINE.set(config.BASELINE_USD)
    if not rows:
        COST_LATEST.set(0)
        return
    latest = max(r["date"] for r in rows)
    per_service = {}
    for r in rows:
        if r["date"] == latest:
            per_service[r["service"]] = per_service.get(r["service"], 0.0) + r["usd"]
    COST_SERVICE.clear()
    for svc, usd in per_service.items():
        COST_SERVICE.labels(service=svc).set(usd)
    COST_LATEST.set(sum(per_service.values()))
