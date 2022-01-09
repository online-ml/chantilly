import io
import os
from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

# Package meta-data.
NAME = 'chantilly'
DESCRIPTION = 'Deployment tool for online machine learning models'
LONG_DESCRIPTION_CONTENT_TYPE = 'text/markdown'
URL = 'https://github.com/creme-ml/chantilly'
EMAIL = 'maxhalford25@gmail.com'
AUTHOR = 'Max Halford'
REQUIRES_PYTHON = '>=3.7.0'

# Import the README and use it as the long-description.
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(here, 'chantilly', '__version__.py')) as f:
    exec(f.read(), about)

setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type=LONG_DESCRIPTION_CONTENT_TYPE,
    author=AUTHOR,
    author_email=EMAIL,
    license='BSD-3',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    packages=find_packages(),
    include_package_data=True,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    zip_safe=False,
    install_requires=[
        'cerberus>=1.3.2',
        'river>=0.9.0',
        'dill>=0.3.1.1',
        'Flask>=1.1.1'
    ],
    extras_require={
        'redis': ['redis>=3.5'],
        'dev': [
            'flake8>=3.7.9',
            'mypy>=0.770',
            'pytest>=5.3.5',
            'pytest-cov>=2.8.1'
        ]
    },
    entry_points={
       'console_scripts': [
           'chantilly=chantilly:cli_hook'
       ],
    }
)
