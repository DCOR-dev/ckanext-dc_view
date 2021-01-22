from os.path import dirname, realpath, exists
from setuptools import setup, find_packages
from codecs import open  # To use a consistent encoding
import sys

author = "Paul Müller"
authors = [author]
description = 'Preview DC data in DCOR '
name = 'ckanext-dc_view'
year = "2020"

sys.path.insert(0, realpath(dirname(__file__))+"/" + "/".join(name.split("-")))
from _version import version  # noqa: E402


setup(
    name=name,
    version=version,
    description=description,
    long_description=open('README.rst').read() if exists('README.rst') else '',
    url='https://github.com/DCOR-dev/ckanext-dc_view',
    author=author,
    author_email='dev@craban.de',
    license='AGPLv3+',
    keywords=["CKAN", "DCOR", "RT-DC"],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_dir={name: name},
    namespace_packages=['ckanext'],
    install_requires=[
        # the "ckan" dependency is implied
        "dclab>=0.27.11",
        "dcor_shared>=0.2.0",
        "matplotlib",
        "numpy>=1.19",
        "pillow",
    ],
    include_package_data=True,
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points='''
        [ckan.plugins]
        dc_view=ckanext.dc_view.plugin:DCViewPlugin
    ''',
    # If you are changing from the default layout of your extension, you may
    # have to change the message extractors, you can read more about babel
    # message extraction at
    # http://babel.pocoo.org/docs/messages/#extraction-method-mapping-and-configuration
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ],
    },
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'License :: OSI Approved :: GNU Affero General Public License v3 or ' \
        + 'later (AGPLv3+)',
        'Programming Language :: Python :: 3',
    ],
)
