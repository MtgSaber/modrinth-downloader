import yaml
from typing import *
from sys import argv

import download


def load_config(yml_path: str) -> Union[Exception, Dict[str, Any]]:
    try:
        with open(yml_path, 'r') as yml:
            return yaml.safe_load(yml)
    except Exception as e:
        return e


def initiate_download_with_config(config: Dict[str, Any]) -> None:
    jobs = config['jobs']
    for job in jobs:
        download.download_with(
            source=job['project-id-list'],
            dest=job['download-destination'],
            mc_version=job['minecraft-version'],
            loader_id=job['mod-loader']
        )


def initiate_download_with_config_file(yml_path: str) -> None:
    load_result = load_config(yml_path)
    if isinstance(load_result, Exception):
        print(f"ERR: got exception while parsing {yml_path}: \"{load_result}\"\n")
        return

    initiate_download_with_config(load_result)


def main():
    if len(argv) != 2:
        print("ERR: this program expects exactly one argument (yml_path).")
        return

    print("Initiating download jobs...")
    initiate_download_with_config_file(argv[1])
    print("Done.")


if __name__ == '__main__':
    main()
