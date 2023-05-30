import json
import os
import time
import datetime
from pathlib import Path
from typing import Optional, List, Dict

import requests

from furry_art_sync.datastore import Datastore
from furry_art_sync.sites.post import Post, PostRating
from furry_art_sync.sites.site import SiteProfile


class FurAffinityPost(Post):
    @property
    def link(self) -> str:
        return self.metadata_raw["link"]

    @property
    def title(self) -> Optional[str]:
        return self.metadata_raw["title"]

    @property
    def description(self) -> Optional[str]:
        return self.metadata_raw["description"]

    @property
    def tags(self) -> Optional[List[str]]:
        return self.metadata_raw["keywords"]

    @property
    def rating(self) -> Optional[PostRating]:
        return {
            "general": PostRating.SAFE,
            "mature": PostRating.MATURE,
            "adult": PostRating.EXPLICIT,
        }[self.metadata_raw["rating"].lower()]

    @property
    def datetime_posted(self) -> Optional[datetime.datetime]:
        return datetime.datetime.fromisoformat(self.metadata_raw["posted_at"])


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
        resp = self._request_from_api(f"/user/{self.username}.json")
        if resp.status_code == 404:
            return False
        return True

    def download_posts(self) -> None:
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
        os.makedirs(directory, exist_ok=True)
        resp = self._request_from_api(f"/user/{self.username}/{folder}.json?full=1&page={page}")
        resp_json = resp.json()
        if not resp_json:
            return False
        for post_data in resp.json():
            post_id = post_data["id"]
            print(f"Downloading post {post_id}")
            metadata_path = directory / f"{post_id}.json"
            if os.path.exists(metadata_path):
                continue
            full_post_resp = self._request_from_api(f"/submission/{post_id}.json")
            full_post_data = full_post_resp.json()
            with open(metadata_path, "w") as f:
                json.dump(full_post_data, f, indent=2)
            image_url = full_post_data["download"]
            image_ext = image_url.split(".")[-1]
            self._download_file(image_url, directory / f"{post_id}.{image_ext}")
        return True

    def _request_from_api(self, path: str) -> requests.Response:
        max_attempts = 10
        attempt = 0
        resp = None
        while attempt < max_attempts:
            resp = requests.get(f"https://faexport.spangle.org.uk/{path.lstrip('/')}")
            if resp.status_code == 503:
                # Cloudflare error
                time.sleep(attempt * 0.5)
                continue
            break
        if resp is None:
            raise Exception("Request did not get made to FAExport API")
        if resp.status_code == 503:
            raise Exception("FA seems to be under cloudflare protection at the moment")
        return resp

    def _download_file(self, image_url: str, target_path: Path) -> None:
        if os.path.exists(target_path):
            return
        resp = requests.get(image_url)
        image_content = resp.content
        with open(target_path, "wb") as f:
            f.write(image_content)

    def build_post(self, submission_file: Path, metadata_file: Path, post_metadata: Dict) -> Post:
        return FurAffinityPost(
            submission_file,
            metadata_file,
            post_metadata,
            self,
        )
