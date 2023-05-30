class PostMatch:
    def __init__(self, match_type: str):
        self.match_type = match_type


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


HASH_PRIORITY = [ManualMatch, MD5Match, HDImageHashMatch, LowDetailImageHashMatch]
