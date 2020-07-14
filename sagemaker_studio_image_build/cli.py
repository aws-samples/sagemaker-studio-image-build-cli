import argparse
import os

import sagemaker_studio_image_build.builder as builder
import logging


def validate_args(args, extra_args):
    # Validate args

    if args.repository:
        # Validate the repository isn't a invalid reference (For e.g. my-repo-name:1:3 fails)
        if args.repository.count(":") > 1:
            raise ValueError(
                f'Error parsing reference: "{args.repository}" is not a valid repository/tag'
            )

    # Validate extra_args
    for idx, extra_arg in enumerate(extra_args):
        # Validate that the path to the Dockerfile is within the PWD.
        if extra_args == "-f" or extra_arg == "--file" and idx + 1 < len(extra_args):
            file_value = extra_args[idx + 1]
            if not os.path.realpath(file_value).startswith(os.getcwd()):
                raise ValueError(
                    f"The value of the -f/file argument [{file_value}] is outside the working directory [{os.getcwd()}]"
                )


def get_role(args):
    if args.role:
        return args.role

    try:
        # The SDK logs a warning for not having pandas and this is the only way to suppress it.
        # https://github.com/aws/sagemaker-python-sdk/issues/1696
        logging.basicConfig(level=logging.CRITICAL)
        import sagemaker

        logging.basicConfig(level=logging.INFO)
        # arn:aws:iam::$account_id:role/$path/$name -> $path/$name
        return "/".join(sagemaker.get_execution_role().split(":")[-1].split("/")[1:])
    except ValueError as e:
        raise ValueError(
            "Unable to determine execution role. Please provide via the --role argument",
            e,
        )


def build_image(args, extra_args):
    validate_args(args, extra_args)

    builder.build_image(
        args.repository, get_role(args), args.bucket, extra_args, log=not args.no_logs
    )


def main():

    parser = argparse.ArgumentParser(
        description="A command line interface for building Docker images in SageMaker Studio "
        "using AWS CodeBuild and pushing to Amazon ECR"
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    build_parser = subparsers.add_parser(
        "build",
        help="Use AWS CodeBuild to build a Docker image and push to Amazon ECR",
    )
    build_parser.add_argument(
        "--repository",
        help="The ECR repository:tag for the image (default: sagemaker-studio-${domain_id}:latest)",
    )
    build_parser.add_argument(
        "--role",
        help=f"The IAM role name for CodeBuild to use (default: the Studio execution role).",
    )
    build_parser.add_argument(
        "--bucket",
        help="The S3 bucket to use for sending data to CodeBuild (if None, use the SageMaker SDK default bucket).",
    )
    build_parser.add_argument(
        "--no-logs",
        action="store_true",
        help="Don't show the logs of the running CodeBuild build",
    )
    build_parser.set_defaults(func=build_image)

    args, unknown = parser.parse_known_args()
    if args.subcommand is None:
        parser.print_help()
    else:
        args.func(args, unknown)


if __name__ == "__main__":
    main()
