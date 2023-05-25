import os

from furry_art_sync.sites.site import SiteProfile


class Datastore:
    STORE_DIR = "store"

    def __init__(self):
        os.makedirs(self.STORE_DIR, exist_ok=True)

    def save_profile(self, profile: SiteProfile) -> None:
        pass  # TODO
