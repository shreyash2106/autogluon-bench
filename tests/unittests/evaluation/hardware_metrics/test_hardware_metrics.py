import datetime
import os
import unittest
from unittest.mock import MagicMock, call, patch

import yaml

from src.autogluon.bench.eval.hardware_metrics import hardware_metrics
from src.autogluon.bench.eval.hardware_metrics.hardware_metrics import (
    get_hardware_metrics,
    get_instance_id,
    get_instance_util,
    get_job_ids,
    get_metrics,
)

test_dir = os.path.dirname(__file__)
config_file = os.path.join(test_dir, "test_config.yaml")
if not config_file:
    raise ValueError("Invalid Config File")
with open(config_file, "r") as f:
    config = yaml.safe_load(f)

hardware_metrics.aws_account_id = config["CDK_DEPLOY_ACCOUNT"]
hardware_metrics.aws_account_region = config["CDK_DEPLOY_REGION"]


class TestHardwareMetrics(unittest.TestCase):
    def test_get_job_ids(self):
        job_ids = get_job_ids(config)
        self.assertEqual(job_ids, ["123456-abc-efg", "010101-xxx-zzz"])

    @patch("boto3.client")
    def test_get_instance_id(self, mock_client):
        job_ids = get_job_ids(config)
        batch_client, ecs_client = MagicMock(), MagicMock()
        mock_client.side_effect = [batch_client, ecs_client]
        mock_batch_response = {
            "jobs": [
                {
                    "container": {
                        "containerInstanceArn": "abc",
                        "taskArn": "arn:aws:ecs:us-east-2:123456789:task/agbenchcomputeenvironmen-DhbZ6yaLr_Batch/b3bb44aa78f",
                    }
                }
            ]
        }
        batch_client.describe_jobs.return_value = mock_batch_response

        mock_ecs_response = {"containerInstances": [{"ec2InstanceId": 12345}]}
        ecs_client.describe_container_instances.return_value = mock_ecs_response
        instance_id = get_instance_id(job_ids[0])
        self.assertEqual(instance_id, 12345)
        cluster = f"arn:aws:ecs:{hardware_metrics.aws_account_region}:{hardware_metrics.aws_account_id}:cluster/agbenchcomputeenvironmen-DhbZ6yaLr_Batch"
        ecs_client.describe_container_instances.assert_called_once_with(cluster=cluster, containerInstances=["abc"])

    @patch("boto3.client")
    def test_get_instance_util(self, mock_client):
        cloudwatch_client = MagicMock()
        mock_client.side_effect = [cloudwatch_client]
        mock_cloudwatch_response = {
            "Label": "CPUUtilization",
            "Datapoints": [
                {"Timestamp": datetime.datetime(2023, 7, 12, 17, 39), "Average": 11.472356376239336, "Unit": "Percent"}
            ],
            "ResponseMetadata": {
                "RequestId": "93ed0de6-7f3c-4af8-8650-2310042c97f8",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                    "x-amzn-requestid": "93ed0de6-7f3c-4af8-8650-2310042c97f8",
                    "content-type": "text/xml",
                    "content-length": "512",
                    "date": "Wed, 12 Jul 2023 18:19:56 GMT",
                },
                "RetryAttempts": 0,
            },
        }
        cloudwatch_client.get_metric_statistics.return_value = mock_cloudwatch_response
        self.assertEqual(
            get_instance_util(
                "1234",
                "CPUUtilization",
                datetime.datetime(2023, 7, 12, 17, 39),
                datetime.datetime(2023, 7, 12, 16, 39),
            ),
            cloudwatch_client.get_metric_statistics.return_value,
        )


if __name__ == "__main__":
    unittest.main()
