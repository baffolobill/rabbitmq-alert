from __future__ import annotations

import pathlib
import typing

import yamlenv


def read_yaml(path: str | pathlib.Path) -> dict[str, typing.Any]:
    """Loads config from a YAML file with env interpolation"""
    with open(path) as yaml:
        config_data = yaml.read()
        return yamlenv.load(config_data)


def setup_config(
    config_file: str,
    cli_options: dict[str, typing.Any],
) -> dict[str, typing.Any]:
    if not config_file:
        raise Exception('config_file is required')

    config_path = pathlib.Path(config_file)
    if not config_path.exists():
        raise Exception('config file does not exist')

    config_data = read_yaml(config_path)

    for cli_param, value in cli_options.items():
        if not value:
            continue

        section, param = cli_param.split('_', maxsplit=1)
        if section in ('general', 'telegram'):
            config_data[section][param] = value
        else:
            raise Exception(f'Unknown cli option: {cli_param}')

    return config_data
