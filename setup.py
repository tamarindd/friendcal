from setuptools import find_packages, setup

setup(
    name="friendtracker",
    install_requires=["dateparser"],
    packages=find_packages(),
    entry_points={"console_scripts": ["friendtracker=friendtracker.tracker:main"]},
)
