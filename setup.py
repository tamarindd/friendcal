from setuptools import setup

setup(
  name='friendtracker',
  install_requires=['dateparser'],
  entry_points={'console_scripts': ['friendtracker=friendtracker.tracker:main']}
)
