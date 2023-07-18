import csv
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import boto3
import os
import typer
import yaml

cloudwatch_client = None
metrics_list = []


def get_instance_ids(config_file: str):
    if not config_file:
        raise ValueError("Invalid Config File")
    logger.info(f"Getting hardware metrics for jobs under config file: {config_file}")
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    aws_account_id = config.get("CDK_DEPLOY_ACCOUNT")
    aws_account_region = config.get("CDK_DEPLOY_REGION")
    job_ids = list(config.get("job_configs", {}).keys())
    batch_client = boto3.client("batch", region_name=f"{aws_account_region}")
    ecs_client = boto3.client("ecs", region_name=f"{aws_account_region}")
    instance_ids = []
    cluster_arns = []
    container_arns = []
    for job_id in job_ids:
        response = batch_client.describe_jobs(jobs=[f"{job_id}"])
        if response:
            container_arn = response["jobs"][0]["container"]["containerInstanceArn"]
            container_arns.append(container_arn)
            cluster_arn = response["jobs"][0]["container"]["taskArn"].split("/")
            cluster = f"arn:aws:ecs:{aws_account_region}:{aws_account_id}:cluster/" + cluster_arn[1]
            cluster_arns.append(cluster)
    for i in range(len(cluster_arns)):
        response = ecs_client.describe_container_instances(
            cluster=cluster_arns[i], containerInstances=[container_arns[i]]
        )
        instance_id = response["containerInstances"][0]["ec2InstanceId"]
        instance_ids.append(instance_id)
    return instance_ids


def get_instance_util(instance_id: str, metric: str, statistics: Optional[List[str]] = ["Average"]) -> dict:
    return cloudwatch_client.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName=metric,
        Dimensions=[
            {"Name": "InstanceId", "Value": instance_id},
        ],
        Statistics=statistics,
        StartTime=datetime.now() - timedelta(hours=1),
        EndTime=datetime.now(),
        Period=120,
    )


def results_to_csv():
    csv_headers = ["InstanceID", "Metric", "Timestamp", "Statistic", "Unit"]
    file_dir = os.path.dirname(__file__)
    csv_location =  os.path.join(file_dir, "hardware_metrics.csv")
    with open(csv_location, "w", newline="") as csvFile:
        writer = csv.DictWriter(csvFile, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(metrics_list)


def format_metrics(instance_metrics: dict, instance_id: str, statistics: Optional[List[str]] = ["Average"]):
    output_dict = {}
    output_dict["InstanceID"] = instance_id
    output_dict["Metric"] = instance_metrics["Label"]
    for i in range(len(instance_metrics["Datapoints"])):
        for stat in statistics:
            try:    
                output_dict["Timestamp"].append(
                    instance_metrics["Datapoints"][i]["Timestamp"].strftime("%m/%d/%Y: %H:%M:%S")
                )
                output_dict["Statistic"].append([f"{stat}", instance_metrics["Datapoints"][i][f"{stat}"]])
            except KeyError:
                output_dict["Timestamp"] = [
                    instance_metrics["Datapoints"][i]["Timestamp"].strftime("%m/%d/%Y: %H:%M:%S")
                ]
                output_dict["Statistic"] = [[f"{stat}", instance_metrics["Datapoints"][i][f"{stat}"]]]
    output_dict["Unit"] = instance_metrics["Datapoints"][i]["Unit"]
    return output_dict


def get_hardware_metrics(
    config_file: str = typer.Option(None, "--config-file", help="Path to YAML config file containing job ids."),
):
    instance_ids = get_instance_ids(config_file)
    global cloudwatch_client
    cloudwatch_client = boto3.client("cloudwatch", region_name="us-east-2")
    global metrics_list
    for instance_id in instance_ids:
        cpu_util = get_instance_util(instance_id, "CPUUtilization")
        metrics_list.append(format_metrics(cpu_util, instance_id))

        ebs_write_ops = get_instance_util(instance_id, "EBSWriteOps")
        metrics_list.append(format_metrics(ebs_write_ops, instance_id))

        ebs_read_ops = get_instance_util(instance_id, "EBSReadOps")
        metrics_list.append(format_metrics(ebs_read_ops, instance_id))
    results_to_csv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()
app.command()(get_hardware_metrics)


if __name__ == "__main__":
    app()
