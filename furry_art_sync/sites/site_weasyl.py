from furry_art_sync.sites.site import SiteProfile


class WeasylSiteProfile(SiteProfile):  # TODO
    def __init__(self, username: str) -> None:
        self.username = username

    def profile_link(self) -> str:
        return f"https://weasyl.com/~{self.username}"

    @classmethod
    def user_setup_profile(cls) -> "SiteProfile":
        raw_username = input("Please enter your Weasyl username: ")
        username = raw_username.lower()
        return cls(username)
