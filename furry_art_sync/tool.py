import os.path
from functools import cache
from typing import Dict, List

from furry_art_sync.datastore import Datastore
from furry_art_sync.sites.post import Post
from furry_art_sync.sites.post_match import PostMatch, HASH_PRIORITY
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
        comparison = ProfileComparison(fa_profile, weasyl_profile)
        print(f"You have {len(comparison.source_posts())} posts on FA")
        print(f"You have {len(comparison.target_posts())} posts on Weasyl")
        for fa_post, match_dict in comparison.matched_posts().items():
            if match_dict:
                print(f"MATCH: {fa_post.link} matches {len(match_dict)} posts on weasyl:")
                for weasyl_post, match in match_dict.items():
                    print(f"- {weasyl_post.link}: {match.match_type}")
            else:
                print(f"NO MATCH: {fa_post.link}")
        print("Unmatched posts from source: ")
        for fa_post in comparison.unmatched_source_posts():
            print(f"- {fa_post.link} \"{fa_post.title}\"")
        print("Unmatched posts from target: ")
        for weasyl_post in comparison.unmatched_target_posts():
            print(f"- {weasyl_post.link} \"{weasyl_post.title}\"")
        print("---")
        weasyl_upload_class = weasyl_profile.uploader_class()
        if not weasyl_upload_class:
            print("No uploader is configured for this target, so cannot automatically sync your gallery")
            return
        upload_option_resp = input("Would you like to upload missing posts to Weasyl? [yN] ")
        if upload_option_resp.lower() not in ["y", "yes"]:
            print("Okay, we will not sync your gallery")
            return
        weasyl_uploader = weasyl_upload_class.user_setup_uploader(weasyl_profile)
        fa_unmatched = sorted(comparison.unmatched_source_posts(), key=lambda post: post.datetime_posted)
        for fa_post in fa_unmatched:
            print(f"This post exists on FA, but not Weasyl: {fa_post.link}, \"{fa_post.title}\"")
            upload_post_resp = input("Would you like to upload that post to Weasyl? [yN]")
            if upload_post_resp.lower() in ["y", "yes"]:
                weasyl_post = weasyl_uploader.upload_post(fa_post)
                print(f"Post uploaded: {weasyl_post.link}")
            print("--")
        print("All done!")


class ProfileComparison:
    def __init__(self, source: SiteProfile, target: SiteProfile) -> None:
        self.source = source
        self.target = target
        self.has_downloaded = False

    def download(self) -> None:
        if self.has_downloaded:
            return
        self.source.download_posts()
        self.target.download_posts()

    @cache
    def source_posts(self) -> List[Post]:
        self.download()
        return self.source.list_local_posts()

    @cache
    def target_posts(self) -> List[Post]:
        self.download()
        return self.target.list_local_posts()

    @cache
    def matched_posts(self) -> Dict[Post, Dict[Post, PostMatch]]:
        results = {}
        source_posts = self.source_posts()
        target_posts = self.target_posts()
        for source_post in sorted(source_posts, key=lambda post: post.link):
            match_dict = source_post.matches_any_posts(target_posts)
            match_dict_filtered: Dict[Post, PostMatch] = {
                post: match for post, match in match_dict.items() if match is not None
            }
            if not match_dict_filtered:
                results[source_post] = {}
                continue
            best_match_priority = min(match.priority() for match in match_dict_filtered.values())
            best_matches = {
                post: match for post, match in match_dict_filtered.items() if match.priority() == best_match_priority
            }
            # TODO: Ensure each target post is only matched to once?
            results[source_post] = best_matches
            if best_matches:
                print(f"MATCH: {source_post.link} matches {len(best_matches)} posts on target:")
                for target_post, match in best_matches.items():
                    print(f"- {target_post.link}: {match.match_type}")
            else:
                print(f"NO MATCH: {source_post.link}")
        return results

    def run(self) -> None:
        pass

    @cache
    def unmatched_source_posts(self) -> List[Post]:
        matched_posts = self.matched_posts()
        return [
            post for post, matches in matched_posts.items() if not matches
        ]

    @cache
    def unmatched_target_posts(self) -> List[Post]:
        target_posts = set(self.target_posts())
        for matches in self.matched_posts().values():
            target_posts -= set(matches.keys())
        return list(target_posts)
