# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

- Sending a `GET` request to `/api/init` now returns more information, including the version of `river` that is being used.
- [Cerberus](https://docs.python-cerberus.org/en/stable/index.html) is used instead of [Marshmallow](https://marshmallow.readthedocs.io/en/stable/) for input validation, which slightly modifies the contents of error messages.
- The `features` field can now contain text input. Before the only possibility was to pass a dictionary.
- Migrated from using `creme` to the evolved project under the new name `river` - 2022-01-09

## [0.2.0](https://pypi.org/project/chantilly/0.2.0/) - 2020-05-02

- It is now possible to use [Redis](https://redis.io/) as a storage backend.
- A few bugs that only arise in production have been fixed.

## [0.1.0](https://pypi.org/project/chantilly/0.1.0/) - 2020-03-12

First stable release.
