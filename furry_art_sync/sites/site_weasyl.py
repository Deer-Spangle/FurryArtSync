import datetime
from pathlib import Path
from typing import List, Dict, Optional, Type

import gallery_dl
import requests

from furry_art_sync.datastore import Datastore
from furry_art_sync.sites.post import Post, PostRating
from furry_art_sync.sites.site import SiteProfile, SiteUploader


class WeasylPost(Post):
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
        return self.metadata_raw["tags"]

    @property
    def rating(self) -> Optional[PostRating]:
        return {
            "general": PostRating.SAFE,
            "mature": PostRating.MATURE,
            "explicit": PostRating.EXPLICIT,
        }[self.metadata_raw["rating"].lower()]

    @property
    def datetime_posted(self) -> Optional[datetime.datetime]:
        return datetime.datetime.fromisoformat(self.metadata_raw["posted_at"])


class WeasylUploader(SiteUploader):

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @classmethod
    def user_setup_uploader(cls, site_profile: "WeasylSiteProfile") -> "WeasylUploader":
        return cls(site_profile.api_key)

    def upload_post(self, post: "Post") -> "Post":
        upload_rating = {
            PostRating.SAFE: 10,
            PostRating.MATURE: 30,
            PostRating.EXPLICIT: 40,
        }.get(post.rating, 40)
        tags = post.tags or []
        tags_modified = False
        while len(tags) < 2:
            print("ERROR: Weasyl requires at least 2 tags on submissions.")
            new_tags = input("Please enter at least 2 tags, separated by commas")
            tags = [tag.strip().replace(" ", "_") for tag in new_tags.split(",")]
            tags_modified = True
        if tags_modified:
            print(f"Tags have been set to {tags} for Weasyl upload")
        data = {
            "title": post.title,
            "rating": upload_rating,
            "content": post.description,
            "tags": " ".join(tags),
        }
        files = {
            "submitfile": open(post.file_path, "rb"),
        }
        post_type = {
            "jpg": "visual",
            "jpeg": "visual",
            "png": "visual",
            "gif": "visual",
            "pdf": "literary",
            "txt": "literary",
            "mp3": "multimedia",
            "swf": "multimedia",
        }.get(post.file_ext)
        if post_type is None:
            raise ValueError(f"This post file type, \".{post.file_ext}\" is not supported on Weasyl")
        url = f"https://weasyl.com/submit/{post_type}"
        if post_type in ["literary", "multimedia"]:
            files["coverfile"] = None  # TODO
        resp = requests.post(
            url,
            data=data,
            files=files,
            headers={
                "Referer": url,
                "Origin": "https://www.weasyl.com",
                "Host": "www.weasyl.com",
                "X-Weasyl-API-Key": self.api_key,
              },
        )
        # TODO: Check resp, find submission link


class WeasylSiteProfile(SiteProfile):
    SITE_DIR = "weasyl"

    def __init__(self, username: str, api_key: str) -> None:
        self.username = username
        self.api_key = api_key

    def profile_directory(self) -> Path:
        return Path(Datastore.STORE_DIR) / self.SITE_DIR / self.username

    def profile_link(self) -> str:
        return f"https://weasyl.com/~{self.username}"

    def validate(self) -> bool:
        resp = requests.get(self.profile_link())
        if resp.status_code == 404:
            print("Error: Weasyl user does not exist")
            return False
        api_resp = requests.get(
            "https://weasyl.com/api/whoami",
            headers={
                "X-Weasyl-API-Key": self.api_key
            }
        )
        if api_resp.status_code != 200:
            print("Error: Failure authenticating to Weasyl API")
            return False
        api_data = api_resp.json()
        if "error" in api_data:
            print(f"Error: Weasyl API returned error: {api_data['error']}")
            return False
        return True

    def configure_gallery_dl(self) -> None:
        gallery_dl.config.set(("extractor",), "filename", "{submitid}.{extension}")
        gallery_dl.config.set(("extractor", "weasyl"), "metadata", True)
        gallery_dl.config.set(("extractor", "weasyl"), "api-key", self.api_key)

    def gallery_dl_postprocessors(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "metadata",
                "mode": "json",
                "filename": "{submitid}.json",
            }
        ]

    def build_post(self, submission_file: Path, metadata_file: Path, post_metadata: Dict) -> Post:
        return WeasylPost(
            submission_file,
            metadata_file,
            post_metadata,
            self,
        )

    @classmethod
    def user_setup_profile(cls) -> "SiteProfile":
        raw_username = input("Please enter your Weasyl username: ")
        username = raw_username.lower()
        api_key = input("Please go to https://www.weasyl.com/control/apikeys and generate an API key: ")
        return cls(username, api_key)

    def uploader_class(self) -> Optional[Type["SiteUploader"]]:
        return WeasylUploader
