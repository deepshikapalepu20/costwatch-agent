
import datetime as dt
import boto3
from . import config


def get_aws_session():
    """Create a Boto3 session using an optional profile
    or the EC2 instance IAM role."""

    if config.AWS_PROFILE:
        return boto3.Session(
            profile_name=config.AWS_PROFILE,
            region_name=config.AWS_REGION
        )

    return boto3.Session(
        region_name=config.AWS_REGION
    )


def daily_cost_by_service(days=None):
    """Daily unblended cost grouped by AWS service."""
    days = days or config.LOOKBACK_DAYS

    end = dt.date.today()
    start = end - dt.timedelta(days=days)

    session = get_aws_session()
    ce = session.client("ce", region_name="us-east-1")

    resp = ce.get_cost_and_usage(
        TimePeriod={
            "Start": start.isoformat(),
            "End": end.isoformat()
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    rows = []

    for day in resp["ResultsByTime"]:
        for g in day["Groups"]:
            rows.append({
                "date": day["TimePeriod"]["Start"],
                "service": g["Keys"][0],
                "usd": float(
                    g["Metrics"]["UnblendedCost"]["Amount"]
                ),
            })

    if config.SIMULATE:
        # Demo mode: inject an artificial EC2 spike for yesterday
        rows.append({
            "date": (end - dt.timedelta(days=1)).isoformat(),
            "service": "Amazon Elastic Compute Cloud - Compute",
            "usd": 6.40,
        })

    return rows


def ec2_utilization(hours=24):
    """Average CPU and tags for every running EC2 instance."""

    session = get_aws_session()

    ec2 = session.client(
        "ec2",
        region_name=config.AWS_REGION
    )

    cw = session.client(
        "cloudwatch",
        region_name=config.AWS_REGION
    )

    now = dt.datetime.now(dt.timezone.utc)
    out = []

    reservations = ec2.describe_instances(
        Filters=[
            {
                "Name": "instance-state-name",
                "Values": ["running"]
            }
        ]
    )["Reservations"]

    for res in reservations:
        for inst in res["Instances"]:

            stats = cw.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[
                    {
                        "Name": "InstanceId",
                        "Value": inst["InstanceId"]
                    }
                ],
                StartTime=now - dt.timedelta(hours=hours),
                EndTime=now,
                Period=3600,
                Statistics=["Average"],
            )

            pts = [p["Average"] for p in stats["Datapoints"]]

            out.append({
                "instance_id": inst["InstanceId"],
                "type": inst["InstanceType"],
                "tags": {
                    t["Key"]: t["Value"]
                    for t in inst.get("Tags", [])
                },
                "avg_cpu": round(sum(pts) / len(pts), 2)
                if pts else None,
            })

    return out
