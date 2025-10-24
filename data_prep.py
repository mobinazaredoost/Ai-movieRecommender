
"""data_prep.py

A helper script that downloads movie metadata from TMDB (The Movie Database) using their API.
You must obtain a TMDB API key and run this script locally (internet required).

Example:
    python data_prep.py --api_key YOUR_TMDB_API_KEY --out movies_tmdb.csv --max_pages 5

This script fetches popular movies and writes a CSV with columns: movieId, title, genres, description
"""
import requests, csv, argparse, time

API_URL = 'https://api.themoviedb.org/3'

def fetch_movies(api_key, max_pages=5, out='movies_tmdb.csv'):
    session = requests.Session()
    movies = []
    for page in range(1, max_pages+1):
        r = session.get(f"{API_URL}/movie/popular", params={'api_key': api_key, 'page': page})
        r.raise_for_status()
        data = r.json()
        for m in data.get('results', []):
            movie_id = m.get('id')
            title = m.get('title')
            overview = m.get('overview','')
            # fetch genres detail
            genres = []
            for g in m.get('genre_ids', []):
                genres.append(str(g))
            movies.append({'movieId': movie_id, 'title': title, 'genres': '|'.join(genres), 'description': overview})
        time.sleep(0.2)
    # write csv
    with open(out, 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['movieId','title','genres','description'])
        writer.writeheader()
        for m in movies:
            writer.writerow(m)
    print(f"Wrote {len(movies)} movies to {out}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--api_key', required=True)
    parser.add_argument('--max_pages', type=int, default=5)
    parser.add_argument('--out', default='movies_tmdb.csv')
    args = parser.parse_args()
    fetch_movies(args.api_key, args.max_pages, args.out)
