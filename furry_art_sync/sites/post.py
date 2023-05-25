import dataclasses
from typing import Optional, List


@dataclasses.dataclass
class Post:
    file_path: Optional[str]
    title: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
