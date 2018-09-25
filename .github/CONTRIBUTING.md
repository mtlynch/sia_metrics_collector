# Contributor Guide

Thanks for contributing to Sia Metrics Collector!

## Running tests

When making a contribution, please add necessary automated tests to exercise the new functionality. Ensure that your changes don't break any existing tests.

To run tests:

```bash
sudo pip install -r dev_requirements
./build
```

To run the tests in a Docker container, run the following command in any bash environment where Docker is installed:

```bash
./docker_build
```

## Code style conventions

This project follows the [Google Python Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).
