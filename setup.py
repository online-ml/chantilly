from setuptools import find_packages, setup

setup(
    name='chantilly',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'creme>=0.5.0',
        'dill>=0.3.1.1',
        'flask>=1.1.1',
        'marshmallow>=3.5.1'
    ],
    extras_require={
        'dev': [
            'flake8>=3.7.9',
            'mypy>=0.770',
            'pytest>=5.3.5'
        ]
    },
    entry_points={
        'console_scripts': [
            'chantilly=app:cli_hook'
        ],
    },
)
