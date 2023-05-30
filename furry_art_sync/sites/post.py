import hashlib
import os.path
from abc import abstractmethod, ABC
from functools import cached_property

import imagehash
from PIL import Image
from pathlib import Path
from typing import Optional, List, Dict, TYPE_CHECKING

from furry_art_sync.sites.post_match import PostMatch, MD5Match, HDImageHashMatch, LowDetailImageHashMatch

if TYPE_CHECKING:
    from furry_art_sync.sites.site import SiteProfile


class Post(ABC):
    EXTENSIONS_IMAGE = ["png", "gif", "jpg", "jpeg"]
    EXTENSIONS_ANIM = ["gif", "png"]
    EXTENSIONS_VIDEO = ["webm", "mp4"]

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
    def file_ext(self) -> str:
        _, ext = os.path.splitext(self.file_path)
        return ext.lower().removeprefix(".")

    @cached_property
    def is_static_image(self) -> bool:
        if self.file_ext.lower() not in self.EXTENSIONS_IMAGE:
            return False
        with Image.open(self.file_path) as img:
            return not getattr(img, "is_animated", False)

    @cached_property
    def colour_hash(self) -> Optional[imagehash.ImageHash]:
        if not self.is_static_image:
            return None
        with Image.open(self.file_path) as img:
            return imagehash.colorhash(img)

    @cached_property
    def high_fidelity_phash(self) -> Optional[imagehash.ImageHash]:
        if not self.is_static_image:
            return None
        with Image.open(self.file_path) as img:
            return imagehash.phash(img, hash_size=32)

    @cached_property
    def low_fidelity_phash(self) -> Optional[imagehash.ImageHash]:
        if not self.is_static_image:
            return None
        with Image.open(self.file_path) as img:
            return imagehash.phash(img, hash_size=8)

    @cached_property
    def md5_hash(self) -> str:
        with open(self.file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def matches_post(self, other: "Post") -> Optional[PostMatch]:
        if self.md5_hash == other.md5_hash:
            return MD5Match()
        if self.is_static_image and other.is_static_image:
            if self.colour_hash - other.colour_hash < 2:
                if self.high_fidelity_phash - other.high_fidelity_phash < 2:
                    return HDImageHashMatch()
                if self.low_fidelity_phash - other.low_fidelity_phash < 2:
                    return LowDetailImageHashMatch()
        pass  # TODO: Implement for gifs?

    def matches_any_posts(self, others: List["Post"]) -> Dict["Post", PostMatch]:
        return {
            post: self.matches_post(post) for post in others
        }
