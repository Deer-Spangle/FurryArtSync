import hashlib
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Optional, List, Dict, TYPE_CHECKING

from furry_art_sync.sites.post_match import PostMatch

if TYPE_CHECKING:
    from furry_art_sync.sites.site import SiteProfile


class Post(ABC):

    def __init__(self, file_path: Path, metadata_path: Path, metadata_raw: Dict, site_profile: "SiteProfile") -> None:
        self.file_path = file_path
        self.metadata_path = metadata_path
        self.metadata_raw = metadata_raw
        self.site_profile = site_profile
        self._md5_hash: Optional[str] = None

    @property
    @abstractmethod
    def link(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def title(self) -> Optional[str]:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        raise NotImplementedError

    @property
    @abstractmethod
    def tags(self) -> Optional[List[str]]:
        raise NotImplementedError

    @property
    def md5_hash(self) -> str:
        if self._md5_hash is not None:
            return self._md5_hash
        with open(self.file_path, "rb") as f:
            self._md5_hash = hashlib.md5(f.read()).hexdigest()
        return self._md5_hash

    def matches_post(self, other: "Post") -> Optional[PostMatch]:
        if self.md5_hash == other.md5_hash:
            return PostMatch("MD5 hashes match")
        pass  # TODO

    def matches_any_posts(self, others: List["Post"]) -> Dict["Post", PostMatch]:
        return {
            post: self.matches_post(post) for post in others
        }
