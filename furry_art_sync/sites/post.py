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

    def matches_post(self, other: "Post") -> PostMatch:
        pass  # TODO
