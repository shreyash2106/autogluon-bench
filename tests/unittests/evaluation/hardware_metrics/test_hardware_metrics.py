import os
import unittest
from unittest.mock import MagicMock, call, patch

import yaml

from src.autogluon.bench.eval.hardware_metrics.hardware_metrics import (
    get_hardware_metrics,
    get_instance_id,
    get_instance_util,
    get_job_ids,
    get_metrics,
)
from src.autogluon.bench.eval.hardware_metrics import hardware_metrics



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

if __name__ == "__main__":
    unittest.main()
