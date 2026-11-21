from pyspark.sql import SparkSession


def get_spark(nom="ecommerce-lakehouse"):
    return (SparkSession.builder
            .appName(nom)
            .master("local[3]")                      # 3 threads sur 4
            .config("spark.driver.memory", "3g")     # 3 Go de mémoire (PC de 8 Go)
            .config("spark.sql.shuffle.partitions", "16")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.ansi.enabled", "false")   # évite les erreurs sur dates/nombres invalides
            .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
            .config("spark.local.dir", "data/tmp_spark")  # fichiers temporaires de Spark
            .getOrCreate())


if __name__ == "__main__":
    spark = get_spark()
    print(spark.version)
    spark.range(5).show()