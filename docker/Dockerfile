# Specify the base image
FROM openjdk:8-jdk-slim

ARG SPARK_VERSION_ARG=3.5.3
ARG HADOOP_VERSION=3.3.1

ENV BASE_IMAGE=openjdk:8-alpine
ENV SPARK_VERSION=$SPARK_VERSION_ARG

ENV SPARK_HOME=/opt/spark
ENV HADOOP_HOME=/opt/hadoop
ENV PATH=$PATH:$SPARK_HOME/bin

RUN set -ex && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
        bash \
        tini \
        libstdc++6 \
        libglib2.0-0 \
        libc6 \
        libpam-modules \
        krb5-user \
        libkrb5-3 \
        libnss3 \
        openssl \
        wget \
        sed \
        curl && \
    rm -rf /var/lib/apt/lists/* && \
    rm /bin/sh && \
    ln -sv /bin/bash /bin/sh && \
    echo "auth required pam_wheel.so use_uid" >> /etc/pam.d/su && \
    chgrp root /etc/passwd && chmod ug+rw /etc/passwd && \
    rm -rf /root/.cache && rm -rf /var/cache/*

RUN wget -O /spark-${SPARK_VERSION}-bin-without-hadoop.tgz https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-without-hadoop.tgz && \
    tar -xzf /spark-${SPARK_VERSION}-bin-without-hadoop.tgz -C /opt/ && \
    ln -s /opt/spark-${SPARK_VERSION}-bin-without-hadoop $SPARK_HOME && \
    rm -f /spark-${SPARK_VERSION}-bin-without-hadoop.tgz && \
    mkdir -p $SPARK_HOME/work-dir && \
    mkdir -p $SPARK_HOME/spark-warehouse

RUN wget -O /hadoop-${HADOOP_VERSION}.tar.gz https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz && \
    tar -xzf /hadoop-${HADOOP_VERSION}.tar.gz -C /opt/ && \
    ln -s /opt/hadoop-${HADOOP_VERSION} $HADOOP_HOME && \
    rm -f /hadoop-${HADOOP_VERSION}.tar.gz

ENV PATH="$SPARK_HOME/bin:$HADOOP_HOME/bin:$PATH"
ENV SPARK_DIST_CLASSPATH=$HADOOP_HOME/etc/hadoop:$HADOOP_HOME/share/hadoop/common/lib/*:$HADOOP_HOME/share/hadoop/common/*:$HADOOP_HOME/share/hadoop/hdfs:$HADOOP_HOME/share/hadoop/hdfs/lib/*:$HADOOP_HOME/share/hadoop/hdfs/*:$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/yarn:$HADOOP_HOME/share/hadoop/yarn/lib/*:$HADOOP_HOME/share/hadoop/tools/lib/*
ENV SPARK_CLASSPATH=$HADOOP_HOME/etc/hadoop:$HADOOP_HOME/share/hadoop/common/lib/*:$HADOOP_HOME/share/hadoop/common/*:$HADOOP_HOME/share/hadoop/hdfs:$HADOOP_HOME/share/hadoop/hdfs/lib/*:$HADOOP_HOME/share/hadoop/hdfs/*:$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/yarn:$HADOOP_HOME/share/hadoop/yarn/lib/*:$HADOOP_HOME/share/hadoop/tools/lib/*

RUN wget -O $SPARK_HOME/jars/hadoop-azure-${HADOOP_VERSION}.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure/${HADOOP_VERSION}/hadoop-azure-${HADOOP_VERSION}.jar
RUN wget -O $SPARK_HOME/jars/hadoop-azure-datalake-${HADOOP_VERSION}.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure-datalake/${HADOOP_VERSION}/hadoop-azure-datalake-${HADOOP_VERSION}.jar
RUN wget -O $SPARK_HOME/jars/azure-storage-7.0.0.jar https://repo1.maven.org/maven2/com/microsoft/azure/azure-storage/7.0.0/azure-storage-7.0.0.jar
RUN wget -O $SPARK_HOME/jars/azure-data-lake-store-sdk-2.3.6.jar https://repo1.maven.org/maven2/com/microsoft/azure/azure-data-lake-store-sdk/2.3.6/azure-data-lake-store-sdk-2.3.6.jar
RUN wget -O $SPARK_HOME/jars/azure-keyvault-core-1.0.0.jar https://repo1.maven.org/maven2/com/microsoft/azure/azure-keyvault-core/1.0.0/azure-keyvault-core-1.0.0.jar
RUN wget -O $SPARK_HOME/jars/azure-keyvault-core-1.0.0.jar https://repo1.maven.org/maven2/ch/hsr/geohash/1.4.0/geohash-1.4.0.jar

# Copy the entrypoint.sh file to use as the entry point
COPY docker/entrypoint.sh /opt/spark/entrypoint.sh

# Provide executable permissions to the entrypoint file
RUN chmod +x /opt/spark/entrypoint.sh

ENTRYPOINT [ "/opt/spark/entrypoint.sh" ]

# Install Python3 and pip3
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    pip3 install --upgrade pip setuptools pygeohash requests && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /opt/spark/

# Copy the requirements file
COPY requirements.txt /opt/spark/requirements.txt

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Copy the Python application files
COPY ../src/main/python/app.py /opt/spark/app.py
COPY ../src/test/test.py /opt/spark/test.py

# Create the /opt/spark/tmp directory and set permissions
RUN mkdir -p /opt/spark/tmp && chmod -R 777 /opt/spark/tmp

# Specify the Python files to be run
CMD ["bash", "-c", "python3 /opt/spark/app.py && python3 /opt/spark/test.py"]
