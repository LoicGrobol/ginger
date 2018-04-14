'''Release a new version.

Usage:
  release (major|minor|patch|explicit <version>) [--name <name>]

Options:
  --name, -n <name>  A (code?)name for the release
'''

__version__ = '0.0.1'

import json
import datetime
import pathlib
import re
import subprocess
import tempfile

import typing as ty

from collections import defaultdict

import appdirs
import requests

from setuptools.config import read_configuration
from docopt import docopt

CONFIG_PATH = pathlib.Path(appdirs.user_config_dir('diroll', False, __version__))/'config.json'


class Version:
    '''Semver versions.'''

    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def from_string(cls, version_str: str) -> 'Version':
        return cls(*(int(l) for l in version_str.split('.')))

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.patch}'


def main_entry_point(argv=None):
    arguments = docopt(__doc__, version=__version__, argv=argv)

    if arguments["--name"] is None:
        arguments["--name"] = '(Anonymous release)'

    package_dir = pathlib.Path(__file__).resolve().parents[1]

    if git_dirty(package_dir):
        raise Exception(f'Uncommitted changes in {package_dir}.')

    # Get the current version from `setup.cfg`
    package_data = read_configuration(package_dir/'setup.cfg')['metadata']

    package_current_version = Version.from_string(package_data['version'])

    # Increment the appropriate level
    if arguments['major']:
        package_new_version = Version(package_current_version.major+1, 0, 0)
    elif arguments['minor']:
        package_new_version = Version(package_current_version.major,
                                      package_current_version.minor+1, 0)
    elif arguments['patch']:
        package_new_version = Version(package_current_version.major,
                                      package_current_version.minor,
                                      package_current_version.patch+1)
    else:
        package_new_version = Version.from_string(arguments['<version>'])

    # Set the version in `__init__.py`
    init_path = package_dir/package_data['name']/'__init__.py'
    with init_path.open('r') as init_stream:
        init_content = init_stream.read()

    init_content = re.sub(
        rf"__version__\s*=\s*'{package_current_version}'",
        f'__version__ = {package_new_version}',
        init_content,
    )

    with init_path.open('w') as init_stream:
        init_stream.write(init_content)

    # Release in change log
    changelog_path = package_dir/'CHANGELOG.md'
    changelog_str = changelog_path.read_text()

    release_date = datetime.date.today().isoformat()
    new_changelog_str = re.sub(
        (
            r'## \[Unreleased\]' '\n'
            r'\[Unreleased\]: (?P<url>.*?)/compare/.+HEAD'
        ),
        (
            '## [Unreleased]\n'
            fr'[Unreleased]: \g<url>/compare/v{package_new_version}...HEAD' '\n\n'
            fr'## [{package_new_version}] - {release_date}' '\n'
            f'[{package_new_version}]:'
            fr'\g<url>/compare/v{package_current_version}...{package_new_version}'
        ),
        changelog_str
    )

    changelog_path.write_text(new_changelog_str)

    # Commit and push the changes in git
    # Extract the change list from the change log
    changes = log_from_changes(changes_from_log(changelog_str)).replace('###', '##')

    repo_url = package_data["url"]
    changes = (
        f'# {package_new_version}\n'
        + changes
        + '\n\n' 'See the full diff at'
        f'<{repo_url}/compare/v{package_current_version}...v{package_new_version}>' '\n\n'
        'See [the changelog](CHANGELOG.md) for more informations about past releases.'
    )

    git_dir = package_dir/'.git'
    git_options = ['git', '--git-dir', str(git_dir), '--work-tree', str(package_dir)]
    subprocess.run(
        [
            *git_options, 'add',
            str(package_dir/'setup.cfg'),
            str(changelog_path),
            str(init_path),
        ],
        check=True,
    )
    subprocess.run([*git_options, 'commit', '-m', f'Release v{package_new_version}'])

    tag_name = f'v{package_new_version}'
    with tempfile.NamedTemporaryFile(mode='w') as tag_message_file:
        tag_message_file.write(changes)
        tag_message_file.flush()

        subprocess.run(
            [*git_options, 'tag', '-F', tag_message_file.name, '--cleanup=verbatim', tag_name],
            check=True,
        )
        subprocess.run(
            [*git_options, 'push', '--follow-tags', '--atomic'],
            check=True,
        )

    release_name = arguments['--name']
    release_github(repo_url, tag_name, f'{tag_name} {release_name}', changes=changes)


def changes_from_log(changelog: str, *,
                     source_version: str = None,
                     dest_version: str = 'Unreleased') -> ty.Dict:
    # Iter over all non-blank lines in `changelog`
    lines_iter = (l for l in changelog.splitlines() if not l.isspace())
    current_line = next(lines_iter)

    # Search for the start of the version range
    start_re = re.compile(r'##.*{dest_version}'.format(
        dest_version=re.escape(dest_version)))
    while not start_re.match(current_line):
        current_line = next(lines_iter)
    current_line = next(lines_iter)

    # Now read the changes
    res = defaultdict(list)
    current_section = None
    if source_version is None:
        end_re = re.compile(r'##[^#]')
    else:
        end_re = re.compile(r'##.*{re.escape(source_version)}')
    section_re = re.compile(r'###\s*(?P<name>.*)')
    item_re = re.compile(r'\s+\-\s*(?P<content>.*)')
    while not end_re.match(current_line):
        try:
            current_line = next(lines_iter)
        except StopIteration:
            break
        section = section_re.match(current_line)
        if section:
            current_section = section.group('name')
            continue
        item = item_re.match(current_line)
        if item:
            res[current_section].append(item.group('content'))
            continue
    return res


def log_from_changes(changes: ty.Dict) -> str:
    halfway = {title: '\n'.join(f'  - {item}' for item in content)
               for title, content in changes.items()}
    res = '\n\n'.join(f'### {title}\n{content}' for title, content in halfway.items())
    return res


def git_dirty(package_dir):
    git_dir = package_dir/'.git'
    fail = subprocess.run([
        'git',
        '--git-dir', str(git_dir),
        '--work-tree', str(package_dir),
        'diff-index',
        '--quiet', '--cached',
        'HEAD',
    ]).returncode
    return fail


def get_config(config_path=CONFIG_PATH) -> ty.Dict:
    try:
        with config_path.open() as config_stream:
            config_dict = json.load(config_stream)
    except FileNotFoundError:
        config_dict = {"access": {}}
        set_config(config_dict, config_path)
    return config_dict


def set_config(config_dict: ty.Dict, config_path=CONFIG_PATH):
    if not config_path.exists():
        config_path.parent.mkdir(parents=True)

    with config_path.open('w') as config_stream:
        json.dump(config_dict, config_stream)


def get_github_token(url):
    config = get_config()
    try:
        username, token = config["access"][url]
    except KeyError:
        print(f"No access for {url} yet.")
        username = input(f"User name for {url}: ")
        token = input(f"Token for {url} (get one from https://github.com/settings/tokens/new): ")
        config["access"][url] = (username, token)
        set_config(config)
    return username, token


def release_github(repo_url, tag, name, changes):
    auth = get_github_token(repo_url)
    url = repo_url.replace('github.com', 'api.github.com/repos') + '/releases'
    r = requests.post(url, auth=auth, data=json.dumps({
        "tag_name": tag,
        "name": name,
        "body": changes
    }))


if __name__ == '__main__':
    main_entry_point()
