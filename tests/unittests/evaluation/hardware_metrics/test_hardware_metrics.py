import unittest
from unittest import mock
from unittest.mock import call
import os
import yaml

PER_DATASET_TEST_CSV_PATH = "random_csv.csv"
ALL_DATASETS_COMBINED_TEST_CSV_PATH = "random_csv2.csv"

from src.autogluon.bench.eval.hardware_metrics.hardware_metrics import get_metrics, get_hardware_metrics, get_instance_id, get_instance_util, get_job_ids

test_dir = os.path.dirname(__file__)
path_to_test_config = os.path.join(test_dir, "test_config.yaml")

class TestHardwareMetrics(unittest.TestCase):
    def test_get_job_ids(self):
        config_file = path_to_test_config
        if not config_file:
            raise ValueError("Invalid Config File")
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        job_ids = get_job_ids(config)
        self.assertEqual(job_ids, ['123456-abc-efg', '010101-xxx-zzz'])
        

if __name__ == "__main__":
    unittest.main()
