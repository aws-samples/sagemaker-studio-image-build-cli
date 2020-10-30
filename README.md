## SageMaker Docker Build

[![Version](https://img.shields.io/pypi/v/sagemaker-studio-image-build.svg)](https://pypi.org/project/sagemaker-studio-image-build/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This is a CLI for building Docker images in SageMaker Studio using AWS CodeBuild.  

### Usage

Navigate to the directory containing the Dockerfile and simply do:

```bash
sm-docker build .
```
 

Any additional arguments supported with `docker build` are supported

```bash
sm-docker build . --file /path/to/Dockerfile --build-arg foo=bar
```

By default, the image will be pushed to a repository `sagemakerstudio` with the tag `latest`, and use the Studio App's execution role and the default SageMaker Python SDK S3 bucket

These can be overridden with the relevant CLI options.

```bash
sm-docker build . --repository mynewrepo:1.0 --role MyRoleName 
``` 

The CLI will take care of packaging the current directory and uploading to S3, creating a CodeBuild project, starting a build with the S3 artifacts, tailing the build logs, and uploading the built image to ECR.


### Installing

Install the CLI using pip.
```bash
pip install sagemaker-studio-image-build
```

Ensure the execution role has a trust policy with CodeBuild.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "codebuild.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

The following permissions are required in the execution role to execute a build in CodeBuild and push the image to ECR

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "codebuild:DeleteProject",
                "codebuild:CreateProject",
                "codebuild:BatchGetBuilds",
                "codebuild:StartBuild"
            ],
            "Resource": "arn:aws:codebuild:*:*:project/sagemaker-studio*"
        },
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogStream",
            "Resource": "arn:aws:logs:*:*:log-group:/aws/codebuild/sagemaker-studio*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:GetLogEvents",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:log-group:/aws/codebuild/sagemaker-studio*:log-stream:*"
        },
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecr:CreateRepository",
                "ecr:BatchGetImage",
                "ecr:CompleteLayerUpload",
                "ecr:DescribeImages",
                "ecr:DescribeRepositories",
                "ecr:UploadLayerPart",
                "ecr:ListImages",
                "ecr:InitiateLayerUpload",
                "ecr:BatchCheckLayerAvailability",
                "ecr:PutImage"
            ],
            "Resource": "arn:aws:ecr:*:*:repository/sagemaker-studio*"
        },
        {
            "Effect": "Allow",
            "Action": "ecr:GetAuthorizationToken",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
              "s3:GetObject",
              "s3:DeleteObject",
              "s3:PutObject"
              ],
            "Resource": "arn:aws:s3:::sagemaker-*/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket"
            ],
            "Resource": "arn:aws:s3:::sagemaker*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetRole",
                "iam:ListRoles"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "arn:aws:iam::*:role/*",
            "Condition": {
                "StringLikeIfExists": {
                    "iam:PassedToService": "codebuild.amazonaws.com"
                }
            }
        }
    ]
}

```

### Development

Checkout the repository.

```bash
make install
```

#### Testing locally
To build locally, use one of the example Dockerfiles in the *examples* directory

```bash
ROLE_NAME=<<A role in your account to use in the CodeBuild build job>>
(cd examples/basic_build && sm-docker build . --role ${ROLE_NAME} )
```

```bash
(cd examples/build_with_args && sm-docker build . --role ${ROLE_NAME} --file Dockerfile.args --build-arg BASE_IMAGE=python:3.8 )
```


#### Testing on SageMaker Studio

To build a binary to use on SageMaker Studio, specify an S3 path and use the *s3bundle* target.

```bash
export DEV_S3_PATH_PREFIX=s3://path/to/location
black .
make -k s3bundle
```

From a "System Terminal" in SageMaker Studio

```bash
export DEV_S3_PATH_PREFIX=s3://path/to/location
aws s3 sync ${DEV_S3_PATH_PREFIX}/sagemaker-docker-build/dist . 
pip install sagemaker_studio_image_build-x.y.z.tar.gz
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
