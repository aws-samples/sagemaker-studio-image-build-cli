import json
import os
import random
import string
import sys
import time

import boto3

from sagemaker_studio_image_build.logs import logs_for_build


class TempCodeBuildProject:
    def __init__(self, s3_location, role, repository=None, compute_type=None, vpc_config=None):
        self.s3_location = s3_location
        self.role = role

        self.session = boto3.session.Session()
        self.domain_id, self.user_profile_name = self._get_studio_metadata()
        self.repo_name = None
        self.compute_type = compute_type or "BUILD_GENERAL1_SMALL"
        self.vpc_config = vpc_config

        if repository:
            self.repo_name, self.tag = repository.split(":", maxsplit=1)

        if self.domain_id and self.user_profile_name:
            project_name_prefix = (
                f"sagemaker-studio-{self.domain_id}-{self.user_profile_name}-"
            )
            project_name_prefix = (
                project_name_prefix[:239]
                if len(project_name_prefix) > 239
                else project_name_prefix
            )
            self.project_name = project_name_prefix + "".join(
                random.choices(string.ascii_letters, k=16)
            )
            if not self.repo_name:
                self.repo_name = f"sagemaker-studio-{self.domain_id}"
                self.tag = self.user_profile_name

        else:
            self.project_name = "sagemaker-studio-image-build-" + "".join(
                random.choices(string.ascii_letters, k=16)
            )
            if not self.repo_name:
                self.repo_name = "sagemaker-studio"
                self.tag = "latest"

    def __enter__(self):
        client = self.session.client("codebuild")
        region = self.session.region_name

        caller_identity = self.session.client("sts").get_caller_identity()
        account = caller_identity["Account"]
        partition = caller_identity["Arn"].split(":")[1]

        args = {
            "name": self.project_name,
            "description": f"Build the image for {self.repo_name} in SageMaker Studio",
            "source": {"type": "S3", "location": self.s3_location},
            "artifacts": {"type": "NO_ARTIFACTS"},
            "environment": {
                "type": "LINUX_CONTAINER",
                "image": "aws/codebuild/standard:4.0",
                "computeType": self.compute_type,
                "environmentVariables": [
                    {"name": "AWS_DEFAULT_REGION", "value": region},
                    {"name": "AWS_ACCOUNT_ID", "value": account},
                    {"name": "IMAGE_REPO_NAME", "value": self.repo_name},
                    {"name": "IMAGE_TAG", "value": self.tag},
                ],
                "privilegedMode": True,
            },
            "serviceRole": f"arn:{partition}:iam::{account}:role/{self.role}",
        }

        if self.vpc_config is not None:
            args["vpcConfig"] = self.vpc_config

        client.create_project(**args)
        return self

    def __exit__(self, *args):
        self.session.client("codebuild").delete_project(name=self.project_name)

    def build(self, log=True):
        self._create_repo_if_required()
        id = self._start_build()
        if log:
            logs_for_build(id, wait=True, session=self.session)
        else:
            self._wait_for_build(id)
        image_uri = self._get_image_uri()
        if image_uri:
            print(f"Image URI: {image_uri}")

    def _start_build(self):
        args = {"projectName": self.project_name}
        client = self.session.client("codebuild")

        response = client.start_build(**args)
        return response["build"]["id"]

    def _wait_for_build(self, build_id, poll_seconds=10):
        client = self.session.client("codebuild")
        status = client.batch_get_builds(ids=[build_id])
        while status["builds"][0]["buildStatus"] == "IN_PROGRESS":
            print(".", end="")
            sys.stdout.flush()
            time.sleep(poll_seconds)
            status = client.batch_get_builds(ids=[build_id])
        print()
        print(f"Build complete, status = {status['builds'][0]['buildStatus']}")
        print(f"Logs at {status['builds'][0]['logs']['deepLink']}")

    def _create_repo_if_required(self):
        client = self.session.client("ecr")
        try:
            client.create_repository(repositoryName=self.repo_name)
            print(f"Created ECR repository {self.repo_name}")
        except client.exceptions.RepositoryAlreadyExistsException as e:
            pass

    def _get_image_uri(self):
        client = self.session.client("ecr")
        try:
            repository_uri = client.describe_repositories(
                repositoryNames=[self.repo_name]
            )["repositories"][0]["repositoryUri"]
            return f"{repository_uri}:{self.tag}"
        except Exception as e:
            print(f"Unable to get Image URI. Error: {e}")
            return None

    def _get_studio_metadata(self):
        metadata_file_path = "/opt/ml/metadata/resource-metadata.json"
        if not os.path.exists(metadata_file_path):
            return None, None

        with open(metadata_file_path) as f:
            metadata = json.load(f)

        return metadata.get("DomainId"), metadata.get("UserProfileName")
