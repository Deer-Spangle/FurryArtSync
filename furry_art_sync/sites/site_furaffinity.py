import json
import os
from pathlib import Path

import requests

from furry_art_sync.datastore import Datastore
from furry_art_sync.sites.site import SiteProfile


class FurAffinitySiteProfile(SiteProfile):
    SITE_DIR = "furaffinity"

    def __init__(self, username: str) -> None:
        self.username = username

    def profile_link(self) -> str:
        return f"https://www.furaffinity.net/user/{self.username}"

    def profile_directory(self) -> Path:
        return Path(Datastore.STORE_DIR) / self.SITE_DIR / self.username

    @classmethod
    def user_setup_profile(cls) -> "SiteProfile":
        raw_username = input("Please enter your FurAffinity username: ")
        username = raw_username.lower().replace("_", "")
        return cls(username)

    def validate(self) -> bool:
        resp = requests.get(f"https://faexport.spangle.org.uk/user/{self.username}")
        if resp.status_code == 404:
            return False
        return True

    def download_posts(self) -> None:
        os.makedirs(self.profile_directory(), exist_ok=True)
        page = 1
        while self._download_page("gallery", page):
            page += 1
        page = 1
        while self._download_page("scraps", page):
            page += 1
        print("Download complete")

    def _download_page(self, folder: str, page: int) -> bool:
        print(f"Downloading page {page} of FA {folder} for {self.username}")
        directory = self.profile_directory()
        if folder == "scraps":
            directory = directory / "Scraps"
        resp = requests.get(f"https://faexport.spangle.org.uk/user/{self.username}/{folder}.json?full=1&page={page}")
        resp_json = resp.json()
        if not resp_json:
            return False
        for post_data in resp.json():
            post_id = post_data["id"]
            print(f"Downloading post {post_id}")
            full_post_resp = requests.get(f"https://faexport.spangle.org.uk/submission/{post_id}.json")
            full_post_data = full_post_resp.json()
            with open(directory / f"{post_id}.json", "w") as f:
                json.dump(full_post_data, f)
            image_url = full_post_data["download"]
            image_ext = image_url.split(".")[-1]
            self._download_file(image_url, directory / f"{post_id}.{image_ext}")

    def _download_file(self, image_url: str, target_path: Path) -> None:
        resp = requests.get(image_url)
        image_content = resp.content
        with open(target_path, "wb") as f:
            f.write(image_content)
