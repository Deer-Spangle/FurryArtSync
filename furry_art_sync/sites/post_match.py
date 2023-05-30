from typing import List, Type


class PostMatch:
    def __init__(self, match_type: str):
        self.match_type = match_type

    def priority(self) -> int:
        return HASH_PRIORITY.index(self.__class__)


class ManualMatch(PostMatch):
    def __init__(self):
        super().__init__("manual")


class MD5Match(PostMatch):
    def __init__(self):
        super().__init__("MD5 hashes match")


class HDImageHashMatch(PostMatch):
    def __init__(self):
        super().__init__("HD image hashes match")


class LowDetailImageHashMatch(PostMatch):
    def __init__(self):
        super().__init__("Low detail image hashes match")


HASH_PRIORITY: List[Type[PostMatch]] = [ManualMatch, MD5Match, HDImageHashMatch, LowDetailImageHashMatch]
