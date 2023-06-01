import glob
import json
import os.path
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, TYPE_CHECKING, Optional, Type

import gallery_dl

from furry_art_sync.datastore import Datastore

if TYPE_CHECKING:
    from furry_art_sync.sites.post import Post


class SiteProfile(ABC):

    @abstractmethod
    def validate(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def build_post(self, submission_file: Path, metadata_file: Path, post_metadata: Dict) -> "Post":
        raise NotImplementedError

    def list_local_posts(self) -> List["Post"]:
        metadata_files = glob.glob("**/*.json", root_dir=self.profile_directory(), recursive=True)
        posts = []
        for metadata_file in metadata_files:
            metadata_path = self.profile_directory() / metadata_file
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            submission_pattern = metadata_file.removesuffix("json") + "*"
            submission_file = [
                s for s in glob.glob(submission_pattern, root_dir=self.profile_directory()) if not s.endswith(".json")
            ][0]
            submission_path = self.profile_directory() / submission_file
            posts.append(self.build_post(submission_path, metadata_path, metadata))
        return posts

    def configure_gallery_dl(self) -> None:
        pass  # Sites can optionally override this, to set other gallery dl config

    def gallery_dl_postprocessors(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "metadata",
                "mode": "json",
                "filename": "{id}.json",
            }
        ]

    def download_posts(self) -> None:
        config_path = str(Path(Datastore.STORE_DIR) / "gallery_dl_config.json")
        if not os.path.exists(config_path):
            with open(config_path, "w") as f:
                json.dump({}, f)
        gallery_dl.config.load([config_path], strict=True)
        gallery_dl.config.set(("extractor",), "base-directory", ".")
        gallery_dl.config.set(("extractor",), "directory", self.profile_directory().parts)
        gallery_dl.config.set(("extractor",), "filename", "{id}.{extension}")
        gallery_dl.config.set(("extractor",), "postprocessors", self.gallery_dl_postprocessors())
        self.configure_gallery_dl()
        data_job = gallery_dl.job.DataJob(self.profile_link())
        dl_job = gallery_dl.job.DownloadJob(self.profile_link())
        data_resp = data_job.run()
        dl_resp = dl_job.run()
        print(data_resp)
        print(dl_resp)

    @abstractmethod
    def profile_directory(self) -> Path:
        raise NotImplementedError

    @abstractmethod
    def profile_link(self) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def user_setup_profile(cls) -> "SiteProfile":
        raise NotImplementedError

    def uploader_class(self) -> Optional[Type["SiteUploader"]]:
        return None


class SiteUploader(ABC):

    @classmethod
    @abstractmethod
    def user_setup_uploader(cls, site_profile: SiteProfile) -> "SiteUploader":
        raise NotImplementedError

    @abstractmethod
    def upload_post(self, post: "Post") -> "Post":
        raise NotImplementedError
