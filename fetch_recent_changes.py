import requests
from pathlib import Path
import logging

class RecentChangesFetcher:
    user_groups: dict[str, list[str]] = {}
    user_rights: dict[str, list[str]] = {}
    
    def __init__(self, name: str, api_root: str, article_root: str, logger: logging.Logger) -> None:
        self.name = name
        self.api_root = api_root
        self.article_root = article_root
        self.last_rc_file = Path(f"{name}-rcid.txt")
        self.logger = logger

    def get_user_rights(self, usernames: list[str]) -> list[list[str]]:
        user_rights = self.user_rights
        user_groups = self.user_groups
        query_names = []
        for username in usernames:
            if username not in user_rights:
                query_names.append(username)
        assert len(usernames) <= 50,\
            f"More than 50 users ({usernames}) need to be checked." \
            "This wiki has some serious problems other than non-autopatrolled users editing pages."
        if len(query_names) > 0:
            self.logger.debug("User rights request sent for " + ", ".join(usernames))
            result = requests.get(self.api_root, {
                'action': 'query',
                'list': 'users',
                'ususers': '|'.join(query_names),
                'usprop': 'groups|rights',
                'format': 'json'
            })
            result = result.json()['query']['users']
            for entry in result:
                groups = entry['groups']
                rights = entry['rights']
                name = entry['name']
                user_groups[name] = groups
                user_rights[name] = rights
        result = []
        for username in usernames:
            result.append(user_rights[username])
        return result


    def rc_filter(self, change) -> bool:
        username = change['user']
        user_id = change['userid']
        # always show ip edits
        if user_id == 0:
            return True
        # skip user creation log
        if change['type'] == 'log' and change['pageid'] == 0:
            return False
        # check for autopatrol right
        rights = self.get_user_rights([username])[0]
        return "autopatrol" not in rights


    def load_last_change(self) -> int:
        default: int = -1
        if not self.last_rc_file.exists():
            return default
        with open(self.last_rc_file, "r") as f:
            try:
                return int(f.read())
            except Exception as e:
                self.logger.warn(str(e))
                return default
            
    def save_last_change(self, id: int):
        with open(self.last_rc_file, "w") as f:
            f.write(str(id))


    def change_to_str(self, change) -> str:
        user = change['user']
        title = change['title']
        comment = change['comment']
        if comment.strip() == "":
            comment = "NONE"
        user_link = f'[User:{user}](<{self.article_root}Special:Contributions/{user.replace(" ", "_")}>)'
        article_link = f'[{title}](<{self.article_root + title.replace(" ", "_")}>)'
        if change['type'] == 'edit':
            diff_link = f"[See diff](<{self.article_root}?diff={change['revid']}&oldid={change['old_revid']}>)"
            return f'{user_link} changed {article_link} with comment `{comment}`. {diff_link}.'
        else:
            return user_link + " made a change to " + article_link


    def generate_string(self, changes) -> str:
        users = set(c['user'] for c in changes if c['userid'] != 0)
        users = list(users)
        self.get_user_rights(users)
        strings = []
        for change in changes:
            if not self.rc_filter(change):
                continue
            strings.append(self.change_to_str(change))
        result = "\n".join(strings)
        return result


    def get_recent_changes(self, cutoff_id: int) -> tuple[int, str]:
        self.logger.debug("Recent changes request sent")
        rc = requests.get(self.api_root, {
            # TODO: maybe add timestamp here? not really necessary since 100 edits/min or even 100 edit/hour is a lot
            'action': 'query',
            'list': 'recentchanges',
            'rcnamespace': '*',
            'rcprop': 'user|userid|comment|timestamp|title|ids',
            'rclimit': 100,
            'format': 'json'
        }).json()
        
        all_changes = []
        
        for change in rc['query']['recentchanges']:
            rc_id: int = change['rcid']
            if cutoff_id == -1:
                self.logger.info(f"Cutoff not found. Using {rc_id} as the cutoff.")
                cutoff_id = rc_id
            if rc_id <= cutoff_id:
                # every id that is not seen is taken care of
                break
            all_changes.append(change)
        result = ""
        if len(all_changes) > 0:
            self.logger.info(f"{len(all_changes)} new changes detected.")
            result = self.generate_string(all_changes)
            cutoff_id = all_changes[0]['rcid']
        return cutoff_id, result

