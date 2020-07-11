

.PHONY: clean artifacts release link install test run

release: install lint
	make artifacts

install: clean
	pip install -e ".[dev]"

clean:
	rm -rf build/dist

artifacts: clean
	python setup.py sdist --dist-dir build/dist

lint:
	black --check .

s3bundle: release
	aws --region us-west-2 s3 sync build/dist/ ${DEV_S3_PATH_PREFIX}/sagemaker-docker-build/dist
