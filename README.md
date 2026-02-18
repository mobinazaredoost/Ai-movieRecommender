
# AI Movie Recommender + Sentiment Analyzer (Enhanced)

This enhanced Streamlit project includes:
- Sentiment analysis (Hugging Face transformers)
- Hybrid recommender: content-based (TF-IDF) + simple item-based collaborative filtering using user ratings
- User accounts and ratings stored in SQLite (`ratings.db`)
- `data_prep.py` helper to fetch TMDB data (requires API key)

## How to run
1. Create a virtual environment and install deps:
   ```bash
   pip install -r requirements.txt
   ```
2. (Optional) Replace `data_movies.csv` with a larger TMDB export produced by `data_prep.py`.
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Files added
- `db.py` - sqlite helper for users & ratings (init_db will create `ratings.db` automatically)
- `data_prep.py` - script to download TMDB popular movies (requires API key)
- `recommender.py` - hybrid recommender class (content + collaborative)
- `app.py` - updated Streamlit app with signup/login and rating UX
- `data_movies.csv` - sample small dataset (replace with TMDB/IMDb csv for production)

## Notes & Next improvements
- Passwords are hashed with SHA-256 (suitable for demo). For production, use salted hashing (bcrypt).
- Collaborative recommender is a simple item-based approach; for more accuracy, try matrix factorization (`surprise`, `implicit`) or neighborhood methods.
- Add pagination and movie posters (TMDB provides image URLs) to improve UX.
- Deploy on Streamlit Cloud or Hugging Face Spaces.

