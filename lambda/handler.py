import datetime as dt
import json
import os
 
import boto3
 
 
def lambda_handler(event, context):
    days = int(os.environ.get("LOOKBACK_DAYS", "7"))
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    ce = boto3.client("ce", region_name="us-east-1")
    resp = ce.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
    )
    daily = [
        {"date": d["TimePeriod"]["Start"], "usd": round(float(d["Total"]["UnblendedCost"]["Amount"]), 4)}
        for d in resp["ResultsByTime"]
    ]
    body = {"days": days, "total_usd": round(sum(x["usd"] for x in daily), 4), "daily": daily}
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
