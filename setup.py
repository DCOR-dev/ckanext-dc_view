from setuptools import setup, find_packages

setup(
    # for compatibility with ckanext namespace
    packages=find_packages(),
    namespace_packages=['ckanext'],
)
