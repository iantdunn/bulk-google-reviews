import os
from git import Repo
from termcolor import colored

def get_git_repo(git_root_abs):
    git_path = os.path.join(git_root_abs, '.git')

    if os.path.exists(git_path):
        return Repo(git_root_abs)

    return None


def git_pull(git_root_abs):
    repo = get_git_repo(git_root_abs)
    if not repo:
        print(colored(f'    No .git directory found in {git_root_abs}, skipping git pull', 'yellow'))
        return

    print(colored(f'    Pulling from Git repository found in {git_root_abs}', 'magenta'))

    # Git pull
    origin = repo.remote(name='origin')
    origin.pull(rebase=True)
    print(colored(f'    Pulled latest changes with rebase from remote repository {origin.url}', 'magenta'))


def git_push(git_root_abs, output_path, commit_message="Update Google Maps reviews"):
    repo = get_git_repo(git_root_abs)
    if not repo:
        print(colored(f'    No .git directory found in {git_root_abs}, skipping git push operations', 'yellow'))
        return
    
    print(colored(f'    Pushing to Git repository found in {git_root_abs}', 'magenta'))

    # Git add
    relative_output_path = os.path.relpath(output_path, git_root_abs)
    repo.index.add([relative_output_path])

    # Git commit
    commit = repo.index.commit(commit_message)
    print(colored(f'    Created commit {commit.hexsha[:8]} on branch {repo.active_branch.name}', 'magenta'))

    # Git push
    origin = repo.remote(name='origin')
    origin.push()
    print(colored(f'    Pushed changes to remote repository {origin.url}', 'magenta'))

