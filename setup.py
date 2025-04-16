from setuptools import setup, find_packages

setup(
    author="Peter Pak",
    name="finetune-am",
    version="0.0.1",
    # Loads in local packages
    packages=find_packages(),
    package_data={
        "am": [
            "data/**/*.ini",
        ]
    },
)
