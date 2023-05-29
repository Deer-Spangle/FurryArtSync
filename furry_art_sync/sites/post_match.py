class PostMatch:
    def __init__(self, match_type: str):
        self.match_type = match_type


class ManualMatch(PostMatch):
    def __init__(self):
        super().__init__("manual")
