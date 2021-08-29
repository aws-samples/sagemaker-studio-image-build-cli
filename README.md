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

By default, the CodeBuild project will not run within a VPC, the image will be pushed to a repository `sagemakerstudio` with the tag `latest`, and use the Studio App's execution role and the default SageMaker Python SDK S3 bucket

These can be overridden with the relevant CLI options.

```bash
sm-docker build . --repository mynewrepo:1.0 --role SampleDockerBuildRole --bucket sagemaker-us-east-1-326543455535 --vpc-id vpc-0c70e76ef1c603b94 --subnet-ids subnet-0d984f080338960bb,subnet-0ac3e96808c8092f2 --security-group-ids sg-0d31b4042f2902cd0
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
            "Sid": "ReadAccessToPrebuiltAwsImages",
            "Effect": "Allow",
            "Action": [
                "ecr:BatchGetImage",
                "ecr:GetDownloadUrlForLayer"
            ],
            "Resource": [
                "arn:aws:ecr:*:763104351884:repository/*",
                "arn:aws:ecr:*:217643126080:repository/*",
                "arn:aws:ecr:*:727897471807:repository/*",
                "arn:aws:ecr:*:626614931356:repository/*",
                "arn:aws:ecr:*:683313688378:repository/*",
                "arn:aws:ecr:*:520713654638:repository/*",
                "arn:aws:ecr:*:462105765813:repository/*"
            ]
        },
        {
            "Sid": "EcrAuthorizationTokenRetrieval",
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken"
            ],
            "Resource": [
                "*"
            ]
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

If you need to run your CodeBuild project within a VPC, please add the following actions to your execution role that the CodeBuild Project will assume:

```json
        {
            "Sid": "VpcAccessActions",
            "Effect": "Allow",
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:CreateNetworkInterfacePermission",
                "ec2:DescribeDhcpOptions",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeVpcs"
            ],
            "Resource": "*"
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
