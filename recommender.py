
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from db import get_all_ratings

class HybridRecommender:
    def __init__(self, movies_df):
        self.movies = movies_df.copy().reset_index(drop=True)
        self.movies['combined'] = (self.movies['genres'].fillna('') + ' ' + self.movies['description'].fillna('')).values
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.movies['combined'])
        # map movieId to index
        self.id_to_index = {int(r['movieId']): idx for idx, r in self.movies.iterrows()}

    def content_recommend_by_text(self, text, top_n=10):
        vec = self.vectorizer.transform([text])
        cosine_similarities = linear_kernel(vec, self.tfidf_matrix).flatten()
        related_indices = cosine_similarities.argsort()[::-1]
        recs = []
        for i in related_indices[:top_n]:
            recs.append({'movieId': int(self.movies.loc[i,'movieId']),
                         'title': self.movies.loc[i,'title'],
                         'score': float(cosine_similarities[i])})
        return recs

    def content_recommend_by_title(self, title, top_n=10):
        matches = self.movies[self.movies['title'].str.contains(title, case=False, na=False)]
        if matches.empty:
            return []
        idx = matches.index[0]
        cosine_similarities = linear_kernel(self.tfidf_matrix[idx:idx+1], self.tfidf_matrix).flatten()
        related_indices = cosine_similarities.argsort()[::-1]
        recs = []
        for i in related_indices[1: top_n+1]:
            recs.append({'movieId': int(self.movies.loc[i,'movieId']),
                         'title': self.movies.loc[i,'title'],
                         'score': float(cosine_similarities[i])})
        return recs

    def item_similarity_matrix(self):
        # compute item-item cosine similarity on TF-IDF
        return cosine_similarity(self.tfidf_matrix)

    def collaborative_recommend(self, user_id, top_n=10):
        # build user-item matrix from DB ratings
        ratings = get_all_ratings()
        if not ratings:
            return []
        df = pd.DataFrame(ratings)
        # pivot to user-item
        pivot = df.pivot_table(index='user_id', columns='movie_id', values='rating').fillna(0)
        if user_id not in pivot.index:
            # cold start: return popular or content-based fallback
            return []
        item_sim = self.item_similarity_matrix()
        # compute scores: score = sum(similarity(item, j) * rating_j) over items rated by user
        user_ratings = pivot.loc[user_id]
        scores = {}
        for item_j, rating in user_ratings[user_ratings>0].items():
            if int(item_j) not in self.id_to_index:
                continue
            j_idx = self.id_to_index[int(item_j)]
            sim_row = item_sim[j_idx]
            for i_idx, sim in enumerate(sim_row):
                movie_id = int(self.movies.loc[i_idx,'movieId'])
                scores[movie_id] = scores.get(movie_id, 0.0) + sim * rating
        # remove already rated
        for rated_movie in user_ratings[user_ratings>0].index:
            scores.pop(int(rated_movie), None)
        # sort scores
        ranked = sorted([{'movieId': k, 'score': v, 'title': self.movies[self.movies['movieId']==k]['title'].values[0]} for k,v in scores.items()], key=lambda x: x['score'], reverse=True)
        return ranked[:top_n]
