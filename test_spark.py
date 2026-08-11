"""
Quick verification script for the pyspark-pokemon-battles conda environment.

Run this AFTER activating the environment and setting HADOOP_HOME:
    conda activate pyspark-pokemon-battles
    python test_spark.py

If you see the Pikachu/Charizard table and the success message,
Spark + Hadoop winutils are correctly configured on Windows.
"""

import findspark
findspark.init()

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("PokemonBattleSetupTest")
    .master("local[*]")
    .getOrCreate()
)

df = spark.createDataFrame(
    [("Pikachu", "Electric"), ("Charizard", "Fire")],
    ["name", "type"],
)
df.show()

# Real Parquet write test — this is where things fail without winutils.exe/hadoop.dll
df.write.mode("overwrite").parquet("test_output")
print("Spark + Parquet write working correctly")

spark.stop()
