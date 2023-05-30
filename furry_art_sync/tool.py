from furry_art_sync.datastore import Datastore
from furry_art_sync.sites.site import SiteProfile
from furry_art_sync.sites.site_weasyl import WeasylSiteProfile
from furry_art_sync.sites.site_furaffinity import FurAffinitySiteProfile


class Tool:
    SUPPORTED_SITES = {
        "furaffinity": FurAffinitySiteProfile,
        "weasyl": WeasylSiteProfile,
    }

    def __init__(self):
        self.datastore = Datastore()

    def run(self) -> None:
        print("Welcome to Furry Art Sync. A tool to synchronise your gallery across multiple furry art sites")
        while True:
            print("----")
            print("There are a few things you can do with this tool:")
            print("[1] Download a new site profile")
            print("[2] Check the match between two site profiles")
            print("[q] Quit the application")
            choice = input("What would you like to do? Enter a number to select: ")
            if choice == "1":
                self.download_profile()
            elif choice == "2":
                self.check_match()
            elif choice.lower() in ["q", "quit", "exit"]:
                print("Thank you for using Furry Art Sync")
                break
            else:
                print("I did not understand that choice, sorry.")

    def download_profile(self) -> None:
        while True:
            print("Which site would you like to set up a profile on?")
            site_idx = {str(n + 1): site_name for n, site_name in enumerate(self.SUPPORTED_SITES.keys())}
            for n, site_name in site_idx.items():
                print(f"- [{n}] {site_name}")
            choice = input("Please select a site by entering the number of the site: ")
            if choice.lower() in site_idx.keys():
                site_class = self.SUPPORTED_SITES[site_idx[choice.lower()]]
                break
            elif choice.lower() in self.SUPPORTED_SITES.keys():
                site_class = self.SUPPORTED_SITES[choice.lower()]
                break
            else:
                print("Choice was not recognised.")
        # Set up profile
        while True:
            profile: SiteProfile = site_class.user_setup_profile()
            valid = profile.validate()
            if not valid:
                print("This does not seem to be a valid profile")
                continue
            break
        self.datastore.save_profile(profile)
        print("Profile added")
        print("Downloading profile")
        profile.download_posts()
        self.datastore.save_profile(profile)

    def check_match(self) -> None:
        print("First, let's set up your FA data")
        while True:
            fa_profile: SiteProfile = FurAffinitySiteProfile.user_setup_profile()
            valid = fa_profile.validate()
            if not valid:
                print("This does not seem to be a valid FA profile")
                continue
            break
        print("Okay, now setup your weasyl data")
        while True:
            weasyl_profile: SiteProfile = WeasylSiteProfile.user_setup_profile()
            valid = weasyl_profile.validate()
            if not valid:
                print("This does not seem to be a valid Weasyl profile")
                continue
            break
        fa_posts = fa_profile.list_local_posts()
        weasyl_posts = weasyl_profile.list_local_posts()
        print(f"You have {len(fa_posts)} posts on FA")
        print(f"You have {len(weasyl_posts)} posts on Weasyl")
        for fa_post in sorted(fa_posts, key=lambda post: post.link):
            match_dict = fa_post.matches_any_posts(weasyl_posts)
            match_dict_filtered = {
                post: match for post, match in match_dict.items() if match is not None
            }
            if match_dict_filtered:
                print(f"MATCH: {fa_post.link} matches {len(match_dict_filtered)} posts on weasyl")
            else:
                print(f"NO MATCH: {fa_post.link}")
