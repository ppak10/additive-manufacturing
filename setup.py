from setuptools import setup, find_packages

setup(
    author="Peter Pak",
    name="finetune-am",
    version="0.0.1",
    # Loads in local packages
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "am": [
            "data/**/*.ini",
        ]
    },
    entry_points={
        "console_scripts": [
            "am=am.manage:main",
        ]
    }
)
