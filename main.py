from googlemaps import GoogleMapsScraper
from datetime import datetime
import argparse
import json
import os
from termcolor import colored

def scrape_reviews(input_path, output_path, num_reviews = 20, sort_by = 'newest', debug = False):
    # collect all reviews to write as a single JSON array
    results = []

    with GoogleMapsScraper(debug=debug) as scraper:
        with open(input_path, 'r') as urls_file:
            url = urls_file.readline().strip()

        if url:
            print(colored(f'    Read URL from {input_path}', 'blue'))
        else:
            print(f'    No URL found in {input_path}')
            exit(1)

        ind = {'most_relevant' : 0 , 'newest' : 1, 'highest_rating' : 2, 'lowest_rating' : 3 }
        error = scraper.sort_by(url, ind[sort_by])
        if error != 0:
            exit(error)

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
            if "hours" in relative_date or "days" in relative_date:
                item['relative_date'] = "less than a week ago"
    print(colored('    Processed review data', 'blue'))

    # only write JSON to file if we have reviews
    if results:
        out_path = os.path.join(output_path)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({"reviews": results}, f, ensure_ascii=True, indent=2)

        print(colored(f'    Writing {len(results)} reviews to {output_path}', 'blue'))
    else:
        print(colored('    No reviews found, not writing output file', 'yellow'))
        exit(0)

def main(path, num_reviews = 20, sort_by = 'newest', debug = False, input_file = 'url.txt', output_file = 'output.json'):
    # Create relative path object from path given
    relative_path = os.path.relpath(path)

    # Current file (inside repo)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f'[INFO]     Current script directory: {script_dir}')

    # CD to directory above repo
    scrape_dir = os.path.abspath(os.path.join(script_dir, '..'))
    print(f'[INFO]     Scraping reviews into {relative_path} for all folders in {scrape_dir}')

    # Loop through all folders
    for folder in os.listdir(scrape_dir):
        scrape_path = os.path.abspath(os.path.join(scrape_dir, folder, relative_path))
        # Make sure it exists
        if not os.path.exists(scrape_path):
            print(colored(f'[SKIPPED]  {folder}', 'yellow'))
            print(f'    {scrape_path} not found')
            continue

        input_path = os.path.join(scrape_path, input_file)
        output_path = os.path.join(scrape_path, output_file)

        print(colored(f'[SCRAPING] {folder}', 'green'))
        try:
            scrape_reviews(num_reviews=num_reviews, sort_by=sort_by, debug=debug, input_path=input_path, output_path=output_path)
            print()
        except Exception as e:
            print(colored(f'[ERROR]    Failed to scrape {folder}', 'red'))
            print(f'    {e}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Google Maps reviews scraper.')
    parser.add_argument('-p', '--path', type=str, default='frontend/src/reviews', help='path to the reviews folder (default: frontend/src/reviews)')
    parser.add_argument('-n', '--num', type=int, default=20, help='number of reviews to scrape (default: 20)')
    parser.add_argument('-i', '--input', type=str, default='url.txt', help='input file containing URL (default: url.txt)')
    parser.add_argument('-o', '--output', type=str, default='output.json', help='output file for scraped reviews (default: output.json)')
    parser.add_argument('-s', '--sort', type=str, default='newest', help='most_relevant, newest, highest_rating or lowest_rating (default: newest)')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='run scraper using browser graphical interface')

    args = parser.parse_args()
    main(path=args.path, num_reviews=args.num, sort_by=args.sort, debug=args.debug, input_file=args.input, output_file=args.output)
