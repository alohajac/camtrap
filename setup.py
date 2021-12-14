from setuptools import setup

setup(
    name = "basic_stats",
    version = "0.1",
    author = "Jack Lawrence",
    packages=['basic_stats'],
    install_requires=['picamera', 'gpiozero', 'time', 'datetime', 'sys'],
)