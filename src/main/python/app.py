import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, when
from pyspark.sql.types import StringType
import requests
import geohash2
import time
from pyspark.sql import Row

def create_spark_session():
    """Create a Spark session with optimized memory allocation."""
    return SparkSession.builder \
        .appName("Weather Geohash") \
        .config("spark.executor.memory", "8g") \
        .config("spark.driver.memory", "8g") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-azure:3.3.1,commons-codec:commons-codec:1.15") \
        .config("spark.dynamicAllocation.enabled", "true") \
        .config("spark.dynamicAllocation.minExecutors", "2") \
        .config("spark.dynamicAllocation.maxExecutors", "20") \
        .getOrCreate()

def get_coordinates(city, address, api_key):
    """Fetches latitude and longitude coordinates using the OpenCage API."""
    url = f"https://api.opencagedata.com/geocode/v1/json?q={address}, {city}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if data['results']:
        latitude = data['results'][0]['geometry']['lat']
        longitude = data['results'][0]['geometry']['lng']
        return latitude, longitude
    return None, None

def get_storage_uri():
    """Returns the storage URI for use in other modules."""
    storage_account_name = "stapoleytepolandcentral"
    return f"abfss://sparkbasics@{storage_account_name}.dfs.core.windows.net/m06sparkbasics/"

def process_hotels(spark, api_key, storage_uri):
    """Process hotels DataFrame to update coordinates and generate geohash."""
    # Read the CSV files that are compressed with gzip in the Hotels folder
    df_hotels = spark.read.format("csv") \
        .option("header", "true") \
        .option("compression", "gzip") \
        .load(f"{storage_uri}hotels/*.csv.gz")

    # Check for null values in Latitude and Longitude
    null_locations = df_hotels.filter(df_hotels.Latitude.isNull() | df_hotels.Longitude.isNull())
    print(f"Number of hotels with null coordinates: {null_locations.count()}")  # Print count of null coordinates

    # Process each row with missing coordinates and create updated rows
    updated_rows = []
    for row in null_locations.collect():
        latitude, longitude = get_coordinates(row.City, row.Address, api_key)
        updated_row = row.asDict()
        updated_row['Latitude'] = latitude if latitude is not None else row.Latitude
        updated_row['Longitude'] = longitude if longitude is not None else row.Longitude
        updated_rows.append(Row(**updated_row))
        print(f"Updated row: {updated_row}")  # Print updated row information
        time.sleep(1.5)

    # Create DataFrame with updated rows
    updated_df = spark.createDataFrame(updated_rows) \
                      .withColumnRenamed("Latitude", "Updated_Latitude") \
                      .withColumnRenamed("Longitude", "Updated_Longitude")

    # Update Latitude and Longitude in the original DataFrame
    df_hotels = df_hotels.join(updated_df.select("Id", "Updated_Latitude", "Updated_Longitude"), "Id", "left_outer") \
        .withColumn("Latitude", when(col("Latitude").isNotNull(), col("Latitude")).otherwise(col("Updated_Latitude"))) \
        .withColumn("Longitude", when(col("Longitude").isNotNull(), col("Longitude")).otherwise(col("Updated_Longitude"))) \
        .drop("Updated_Latitude", "Updated_Longitude")

    return df_hotels

def generate_geohash(lat, lon):
    """Generate a 4-character geohash from latitude and longitude."""
    if lat is not None and lon is not None:
        return geohash2.encode(lat, lon, precision=4)
    return None

def main():
    # Load environment variables
    storage_account_name = "your_storage_account_name"
    access_key = "your_access_key"
    api_key = "your_api_key"

    # Create the Azure Storage URI for the "sparkbasics" container (to read) and "data" container (to write)
    storage_uri = get_storage_uri()

    # Establish the Spark session
    spark = create_spark_session()
    
    # Set the access key for Azure Storage
    spark.conf.set(f"fs.azure.account.key.{storage_account_name}.dfs.core.windows.net", access_key)

    # Process hotels data
    df_hotels = process_hotels(spark, api_key, storage_uri)

    # Define UDF and add geohash column
    geohash_udf = udf(generate_geohash, StringType())
    df_hotels_with_geohash = df_hotels.withColumn("Geohash", geohash_udf(df_hotels["Latitude"].cast("float"), df_hotels["Longitude"].cast("float")))

    # Show the first few rows of the hotels DataFrame with geohash
    print("Hotels DataFrame with Geohash:")
    df_hotels_with_geohash.show(truncate=False)

    # Load weather data from the sparkbasics container
    weather_data_path = f"abfss://sparkbasics@{storage_account_name}.dfs.core.windows.net/m06sparkbasics/weather/year=*/month=*/day=*/*.parquet"
    df_weather = spark.read.parquet(weather_data_path)

    # Partition the df_weather DataFrame
    df_weather_partitioned = df_weather.repartition(300, "wthr_date")

    # Add the geohash column to the weather DataFrame
    df_weather_with_geohash = df_weather_partitioned.withColumn("Geohash", geohash_udf(col("lat").cast("float"),col("lng").cast("float")))

    # Perform the left join with hotels DataFrame
    df_joined = df_hotels_with_geohash.join(df_weather_with_geohash, on="Geohash", how="left")

    #Show the first few rows of the Left Joined DataFrame with geohash
    df_joined.limit(10).show(truncate=False)

    # Write the enriched data to the "data" container (Parquet format with partitioning)
    enriched_data_path = f"abfss://data@{storage_account_name}.dfs.core.windows.net/enriched_data/"
    df_joined.write \
        .mode("overwrite") \
        .partitionBy("wthr_date") \
        .parquet(enriched_data_path)

    print("Enriched data saved to Azure Storage.")

    # Stop the Spark session
    spark.stop()

if __name__ == '__main__':
    main()