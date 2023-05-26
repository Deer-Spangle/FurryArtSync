from pathlib import Path
from typing import List, Dict

import gallery_dl
import requests

from furry_art_sync.datastore import Datastore
from furry_art_sync.sites.site import SiteProfile


class WeasylSiteProfile(SiteProfile):  # TODO
    SITE_DIR = "weasyl"

    def __init__(self, username: str) -> None:
        self.username = username

    def profile_directory(self) -> Path:
        return Path(Datastore.STORE_DIR) / self.SITE_DIR / self.username

    def profile_link(self) -> str:
        return f"https://weasyl.com/~{self.username}"

    def validate(self) -> bool:
        resp = requests.get(self.profile_link())
        return resp.status_code != 404

    def configure_gallery_dl(self) -> None:
        gallery_dl.config.set(("extractor",), "filename", "{submitid}.{extension}")

    def gallery_dl_postprocessors(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "metadata",
                "mode": "json",
                "filename": "{submitid}.json",
            }
        ]

    @classmethod
    def user_setup_profile(cls) -> "SiteProfile":
        raw_username = input("Please enter your Weasyl username: ")
        username = raw_username.lower()
        return cls(username)
