from googlemaps import GoogleMapsScraper
from datetime import datetime
import argparse
import json
import os
from termcolor import colored
from git import Repo

def scrape_reviews(input_path, output_path, num_reviews, sort_by, debug):
    # collect all reviews to write as a single JSON array
    results = []

    with GoogleMapsScraper(debug=debug) as scraper:
        with open(input_path, 'r') as urls_file:
            url = urls_file.readline().strip()

        if url:
            print(colored(f'    Read URL from {input_path}', 'blue'))
        else:
            print(f'    No URL found in {input_path}')
            return False

        ind = {'most_relevant' : 0 , 'newest' : 1, 'highest_rating' : 2, 'lowest_rating' : 3 }
        if scraper.sort_by(url, ind[sort_by]) != 0:
            return False

        n = 0
        while n < num_reviews:
            reviews = scraper.get_reviews(n)
            if len(reviews) == 0:
                break

            for r in reviews:
                results.append(r)

            # Log in human-readable format - +1 to start index (inclusive), keep end index (exclusive)
            print(colored(f'    Scraped reviews {n + 1} - {n + len(reviews)}', 'blue'))
            n += len(reviews)

    # process reviews
    for item in results:
        # remove id, n_review_user
        item.pop('id_review', None)
        item.pop('n_review_user', None)

        rd = item.get('retrieval_date')
        if isinstance(rd, datetime):
            item['retrieval_date'] = rd.isoformat()

        # set relative_date less than a week ago to "less than a week ago"
        # current date could be "18 hours ago" or "3 days ago"
        relative_date = item.get('relative_date')
        if relative_date and isinstance(relative_date, str):
            if any(x in relative_date for x in ("second", "minute", "hour", "day")):
                item['relative_date'] = "less than a week ago"
                
    print(colored('    Processed review data', 'blue'))

    # only write JSON to file if we have reviews
    if results:
        out_path = os.path.join(output_path)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({"reviews": results}, f, ensure_ascii=True, indent=2)

        print(colored(f'    Writing {len(results)} reviews to {output_path}', 'blue'))
        return True
    else:
        print(colored('    No reviews found, not writing output file', 'yellow'))
        return False

def git_push(git_root_abs, output_path, commit_message="Update Google Maps reviews"):
    relative_output_path = os.path.relpath(output_path, git_root_abs)
    git_path = os.path.join(git_root_abs, '.git')

    if not os.path.exists(git_path):
        print(colored(f'    No .git directory found in {git_root_abs}, skipping git operations', 'yellow'))
        return

    print(colored(f'    Git repository found in {git_root_abs}', 'magenta'))
    
    try:
        # Git add
        repo = Repo(git_root_abs)
        repo.index.add([relative_output_path])

        # Git commit
        commit = repo.index.commit(commit_message)
        print(colored(f'    Created commit {commit.hexsha[:8]} on branch {repo.active_branch.name}', 'magenta'))

        # Git push
        origin = repo.remote(name='origin')
        origin.push()
        print(colored(f'    Pushed changes to remote repository {origin.url}', 'magenta'))
    except Exception as e:
        print(colored(f'    Git operation failed: {e}', 'red'))

def main(path, num_reviews, sort_by, debug, git, input_file, output_file):
    # Create relative path object from path given
    relative_path = os.path.relpath(path)

    # Current file (inside repo)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f'[INFO]     Current script directory: {script_dir}')

    # CD to directory above repo
    scrape_dir = os.path.abspath(os.path.join(script_dir, '..'))
    print(f'[INFO]     Scraping reviews into {relative_path} for all folders in {scrape_dir}')

    if git:
        print(colored(f'[INFO]     Git operations enabled', 'magenta'))

    if debug:
        print(colored(f'[INFO]     Debug mode enabled - browser GUI will be shown', 'cyan'))

    print()

    # Loop through all folders
    for folder in os.listdir(scrape_dir):
        project_path_abs = os.path.abspath(os.path.join(scrape_dir, folder))
        scrape_path = os.path.join(project_path_abs, relative_path)
        # Make sure it exists
        if not os.path.exists(scrape_path):
            print(colored(f'[SKIPPED]  {folder}', 'yellow'))
            print(f'    {scrape_path} not found\n')
            continue

        input_path = os.path.join(scrape_path, input_file)
        output_path = os.path.join(scrape_path, output_file)

        print(colored(f'[SCRAPING] {folder}', 'green'))

        try:
            success = scrape_reviews(num_reviews=num_reviews, sort_by=sort_by, debug=debug, input_path=input_path, output_path=output_path)
        except Exception as e:
            print(colored(f'[ERROR]    Failed to scrape {folder}', 'red'))
            print(f'    {str(e)}')

        if success and git:
            git_push(project_path_abs, output_path)

        print()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Google Maps reviews scraper.')
    parser.add_argument('-p', '--path', type=str, default='reviews', help='path to the reviews folder (default: reviews)')
    parser.add_argument('-n', '--num', type=int, default=50, help='number of reviews to scrape (default: 50)')
    parser.add_argument('-i', '--input', type=str, default='url.txt', help='input file containing URL (default: url.txt)')
    parser.add_argument('-o', '--output', type=str, default='output.json', help='output file for scraped reviews (default: output.json)')
    parser.add_argument('-s', '--sort', type=str, default='newest', help='most_relevant, newest, highest_rating or lowest_rating (default: newest)')
    parser.add_argument('-g', '--git', dest='git', action='store_true', help='use git to add, commit, and push (re)generated output files')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='run scraper using browser graphical interface')

    args = parser.parse_args()
    main(path=args.path, num_reviews=args.num, sort_by=args.sort, debug=args.debug, git=args.git, input_file=args.input, output_file=args.output)
