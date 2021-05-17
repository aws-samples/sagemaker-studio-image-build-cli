import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

required_packages = ["boto3>=1.10.44, < 2.0", "sagemaker < 3.0"]

setuptools.setup(
    name="sagemaker_studio_image_build",
    version="0.6.0",
    author="Amazon Web Services",
    description="Build Docker Images in Amazon SageMaker Studio using AWS CodeBuild",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aws-samples/sagemaker-studio-image-build-cli",
    packages=["sagemaker_studio_image_build"],
    license="MIT-0",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">=3.6",
    install_requires=required_packages,
    extras_require={"dev": ["black", "pytest"]},
    entry_points={
        "console_scripts": ["sm-docker=sagemaker_studio_image_build.cli:main"]
    },
    include_package_data=True,
    package_data={"sagemaker_studio_image_build": ["*.yml", "data/**"]},
)
