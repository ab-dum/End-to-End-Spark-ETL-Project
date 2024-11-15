import sys
import os
import unittest
from unittest.mock import patch
from pyspark.sql import SparkSession

# Add the main directory to the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../main/python')))

from app import create_spark_session, process_hotels, generate_geohash, get_storage_uri

class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a SparkSession
        cls.spark = create_spark_session()
        # Azure Storage credentials
        cls.storage_account_name = "your_storage_account_name"
        cls.container_name = "your_container_name"
        cls.access_key = "your_access_key"
        cls.api_key = "your_api_key"

        # Set the Azure Storage URI
        cls.storage_uri = get_storage_uri()
        # Set the Spark configuration
        cls.spark.conf.set(f"fs.azure.account.key.{cls.storage_account_name}.dfs.core.windows.net", cls.access_key)

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    @patch('app.get_coordinates')
    def test_get_coordinates_valid(self, mock_get_coordinates):
        # Define the mocked response
        mock_get_coordinates.return_value = (51.5034, -0.1276)
        
        city = "London"
        address = "10 Downing St"
        latitude, longitude = mock_get_coordinates(city, address, self.api_key)  
        self.assertIsNotNone(latitude)
        self.assertIsNotNone(longitude)

    def test_process_hotels(self):
        # Define test data
        data = [
            {"Id": "1", "City": "Istanbul", "Address": "Address 1", "Latitude": 41.0082, "Longitude": 28.9784},
            {"Id": "2", "City": "Ankara", "Address": "Unknown", "Latitude": None, "Longitude": None},
        ]
        
        # Create a test DataFrame
        df_test_hotels = self.spark.createDataFrame(data)

        # Run the process_hotels function
        processed_df = process_hotels(self.spark, self.api_key, self.storage_uri)
        
        # Check the processing results
        self.assertGreater(processed_df.count(), 0)

    def test_generate_geohash(self):
        lat = 51.5034
        lon = -0.1276
        geohash = generate_geohash(lat, lon)
        self.assertIsNotNone(geohash)
        self.assertEqual(len(geohash), 4)  # The geohash should be 4 characters long

if __name__ == '__main__':
    unittest.main()
