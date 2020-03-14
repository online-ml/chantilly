from setuptools import find_packages, setup

setup(
    name='chantilly',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'dill==0.3.1.1',
        'flask==1.1.1',
        'influxdb==5.2.3'
    ],
    entry_points={
        'console_scripts': [
            'chantilly=app:cli_hook'
        ],
    },
)
