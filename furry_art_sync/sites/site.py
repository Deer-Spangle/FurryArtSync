from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from furry_art_sync.sites.post import Post


class SiteProfile(ABC):

    @abstractmethod
    def validate(self) -> bool:
        raise NotImplementedError

    def list_local_posts(self) -> List[Post]:
        pass

    def download_posts(self) -> None:
        pass

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
