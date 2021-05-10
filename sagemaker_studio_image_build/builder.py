import os
import json
import random
import string
import tempfile
import zipfile


import boto3
import logging


def upload_zip_file(repo_name, bucket, extra_args, dir="."):
    """
    1. Zip up the PWD.
    2. Replace placeholders in buildspec.yml and add to the Zip.
    3. Upload to S3.
    """
    if not bucket:
        # The SDK logs a warning for not having pandas and this is the only way to suppress it.
        # https://github.com/aws/sagemaker-python-sdk/issues/1696
        logging.basicConfig(level=logging.CRITICAL)
        import sagemaker.session as session

        logging.basicConfig(level=logging.INFO)

        bucket = session.Session().default_bucket()

    random_suffix = "".join(random.choices(string.ascii_letters, k=16))
    key = f"codebuild-sagemaker-container-{random_suffix}.zip"
    origdir = os.getcwd()
    os.chdir(dir)
    try:
        with tempfile.TemporaryFile() as tmp:
            with zipfile.ZipFile(tmp, "w") as zip:
                # Zip all files in "dir"
                for dirname, _, filelist in os.walk("."):
                    for file in filelist:
                        zip.write(f"{dirname}/{file}")
                # Add buildspec.yml
                data_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "data"
                )
                with tempfile.NamedTemporaryFile() as buildspec:
                    with open(
                        os.path.join(data_dir, "buildspec.template.yml")
                    ) as buildspec_template:
                        buildspec_replaced = buildspec_template.read().replace(
                            "REPLACE_ME_BUILD_ARGS", extra_args
                        )
                        buildspec.write(buildspec_replaced.encode())
                    buildspec.seek(0)
                    zip.write(buildspec.name, "buildspec.yml")
            tmp.seek(0)
            s3 = boto3.session.Session().client("s3")
            s3.upload_fileobj(tmp, bucket, key)
        return (bucket, key)
    finally:
        os.chdir(origdir)


def delete_zip_file(bucket, key):
    s3 = boto3.session.Session().client("s3")
    s3.delete_object(Bucket=bucket, Key=key)


def build_image(repository, role, bucket, compute_type, vpc_config, extra_args, log=True):
    bucket, key = upload_zip_file(repository, bucket, " ".join(extra_args))
    try:
        from sagemaker_studio_image_build.codebuild import TempCodeBuildProject

        with TempCodeBuildProject(f"{bucket}/{key}", role, repository=repository, 
                                    compute_type=compute_type, vpc_config=vpc_config) as p:
            p.build(log)
    finally:
        delete_zip_file(bucket, key)
