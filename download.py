from dateutil import parser
from dataclasses import dataclass
from enum import Enum
from typing import *
from os import path
from sys import argv

import requests


class VersionType(Enum):
    UNKNOWN = 0
    ANY = 1
    ALPHA = 2
    BETA = 3
    RELEASE = 4


version_type_string_ids = {
    VersionType.ALPHA: "alpha",
    VersionType.BETA: "beta",
    VersionType.RELEASE: "release",
}
version_type_by_string_id = {v: k for k, v in version_type_string_ids.items()}


class Loader(Enum):
    FABRIC = 1
    DATAPACK = 2


loader_string_ids = {
    Loader.FABRIC: "fabric",
    Loader.DATAPACK: "datapack",
}
loader_by_string_id = {v: k for k, v in loader_string_ids.items()}


labrinth_base_url = "https://api.modrinth.com/v2"


def get_latest_version_by_id(
        project_id: str,
        mc_version: str,
        loader: Loader = Loader.FABRIC,
        minimum_type: VersionType = VersionType.ANY
) -> Union[Exception, int, dict[str, Any]]:
    try:
        result = requests.get(
            url=labrinth_base_url + f"/project/{project_id}/version?loaders=[\"{loader_string_ids[loader]}\"]&game_versions=[\"{mc_version}\"]"
        )
        if result.status_code == 200:
            return list(sorted(
                list(filter(
                    lambda version: (version_type_by_string_id[version['version_type']].value >= minimum_type.value),
                    result.json()
                )),
                key=lambda version: parser.isoparse(version['date_published']),
                reverse=True
            ))[0]
        return result.status_code
    except Exception as e:
        return e


@dataclass
class UrlDownloadInfo:
    filename: str
    url: str
def get_primary_file_url_for_version(version: dict[str, Any]) -> Union[Exception, UrlDownloadInfo]:
    try:
        primary = list(filter(lambda file: file['primary'], version['files']))[0]
        return UrlDownloadInfo(primary['filename'], primary['url'])
    except Exception as e:
        return e


def dl_file_from_url(url: str, dest_dir: str) -> Union[Exception, int, None]:
    try:
        req = requests.get(url)
        if req.status_code != 200: return req.status_code
        with open(dest_dir, 'wb') as f:
            for chunk in req.iter_content(1024):
                f.write(chunk)
    except Exception as e:
        return e


def download_with(source: str, dest: str, mc_version: str, loader_id: str) -> None:
    with open(source, 'r') as sf:
        mod_ids = list(filter(lambda s: len(s) > 0, [s.strip() for s in sf.readlines()]))
    versions = {mod_id: get_latest_version_by_id(mod_id, mc_version, loader_by_string_id[loader_id]) for mod_id in mod_ids}

    urls = {}
    for mod_id, version in versions.items():
        if isinstance(version, Exception):
            print(f"ERR: got exception while loading version for \"{mod_id}\": \"{str(version)}\"\n")
        elif isinstance(version, int):
            print(f"ERR: received http code {str(version)} while querying for latest version of \"{mod_id}\"\n")
        else:
            urls[mod_id] = get_primary_file_url_for_version(version)

    for mod_id, download_info in urls.items():
        if isinstance(download_info, Exception):
            print(f"ERR: got exception while finding primary file for \"{mod_id}\": \"{str(download_info)}\"\n")
        else:
            result = dl_file_from_url(download_info.url, path.join(dest, download_info.filename))
            if isinstance(result, Exception):
                print(f"ERR: got exception while downloading file \"{download_info.filename}\" for mod \"{mod_id}\" from \"{download_info.url}\"\n")
            elif isinstance(result, int):
                print(f"ERR: got http code {result} while requesting file \"{download_info.filename}\" for mod \"{mod_id}\" from \"{download_info.url}\"\n")


def main():
    if len(argv) != 5:
        print("ERR: This program expects exactly 4 arguments (id source file, download destination, mc version, mod loader).")
        return
    source = argv[1]
    dest = argv[2]
    mc_version = argv[3]
    loader = argv[4]
    download_with(source, dest, mc_version, loader)


if __name__ == '__main__':
    main()
