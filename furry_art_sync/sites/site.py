import json
import os.path
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict

import gallery_dl

from furry_art_sync.datastore import Datastore
from furry_art_sync.sites.post import Post


class SiteProfile(ABC):

    @abstractmethod
    def validate(self) -> bool:
        raise NotImplementedError

    def list_local_posts(self) -> List[Post]:
        pass  # TODO

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
        gallery_dl.config.set(("extractor",), "base-directory", str(self.profile_directory()))
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
