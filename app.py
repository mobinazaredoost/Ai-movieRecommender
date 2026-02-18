import streamlit as st
import pandas as pd
from recommender import HybridRecommender
from sentiment import SentimentAnalyzer
import db, os

db.init_db()

@st.cache_data
def load_movies(path='data_movies.csv'):
    return pd.read_csv(path)

def fetch_user_ratings_from_db(user_id):
    """
    از db.get_user_ratings استفاده می‌کنیم و خروجی را برمی‌گردانیم.
    فرض: db.get_user_ratings(user_id) دیکشنری {movieId: rating} برمی‌گرداند.
    """
    try:
        ur = db.get_user_ratings(user_id)
        normalized = {}
        for k, v in (ur.items() if ur else []):
            try:
                normalized[int(k)] = float(v)
            except Exception:
                normalized[k] = float(v)
        return normalized
    except Exception as e:
     
        st.error("Error reading user ratings from DB.")
        return {}

def find_title_by_movieid(movies_df, movie_id):
    """
    movie_id ممکنه int یا str باشه — این تابع سعی میکنه title رو پیدا کنه.
    """
    try:
        mid_int = int(movie_id)
        match = movies_df[movies_df['movieId'] == mid_int]
    except Exception:
        match = movies_df[movies_df['movieId'].astype(str) == str(movie_id)]

    if not match.empty:
        return match['title'].values[0]
    return None


def login_section():
    st.sidebar.subheader('🔐 Account')

    if 'user' not in st.session_state:
        choice = st.sidebar.selectbox('Have an account?', ['Login','Sign up'])

        if choice == 'Sign up':
            username = st.sidebar.text_input('Username', key='su_user')
            password = st.sidebar.text_input('Password', type='password', key='su_pass')
            if st.sidebar.button('Create account'):
                res = db.create_user(username, password)
                if res.get('error'):
                    st.sidebar.error('⚠️ Username already taken.')
                else:
                    st.sidebar.success('✅ Account created. Please log in.')
        else:
            username = st.sidebar.text_input('Username', key='li_user')
            password = st.sidebar.text_input('Password', type='password', key='li_pass')
            if st.sidebar.button('Login'):
                user = db.authenticate(username, password)
                if user:
                    st.session_state['user'] = user
                    # بعد از ورود، فوراً فچ کردن ریت‌های کاربر
                    st.session_state['user_ratings'] = fetch_user_ratings_from_db(user['id'])
                    st.sidebar.success(f"✅ Logged in as {user['username']}")
                    st.rerun()
                else:
                    st.sidebar.error('❌ Invalid credentials.')
    else:
        st.sidebar.write(f"👤 Logged in as: **{st.session_state['user']['username']}**")
        if st.sidebar.button('Logout'):
   
            for k in ['user', 'user_ratings']:
                if k in st.session_state:
                    del st.session_state[k]
            st.sidebar.success("Logged out.")
            st.rerun()

# ---------- Main ----------
def main():
    st.set_page_config(page_title='AI Movie Recommender + Sentiment Analyzer', layout='wide')
    st.title('🎬 AI Movie Recommender + Sentiment Analyzer')

  
    movies = load_movies()
    rec = HybridRecommender(movies)
    analyzer = SentimentAnalyzer()


    login_section()


    if 'user' in st.session_state and 'user_ratings' not in st.session_state:
        st.session_state['user_ratings'] = fetch_user_ratings_from_db(st.session_state['user']['id'])

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header('🧾 Analyze a review and get recommendations')
        user_text = st.text_area('Write a review, short opinion, or paste a tweet:', height=140)

        btn_col1, btn_col2 = st.columns([1,1])
        with btn_col1:
            if st.button('Analyze sentiment'):
                if user_text.strip():
                    res = analyzer.analyze(user_text)
                    st.success(f"Sentiment: {res['label']} (score: {res['score']:.2f})")
                else:
                    st.info('Write something first.')

        with btn_col2:
            if st.button('Recommend based on text'):
                if user_text.strip():
                    recs = rec.content_recommend_by_text(user_text, top_n=6)
                    st.subheader('🎯 Recommendations (content-based)')
                    for r in recs:
                        st.write(f"**{r['title']}** — score: {r['score']:.3f}")
                else:
                    st.info('Write a review first to base recommendations on.')

        st.markdown('---')
        st.subheader('🎞 Search movie and rate')


        title_query = st.text_input('Search title (partial ok):', key='search_input')


        if st.button('Search'):
            if not title_query or not title_query.strip():
                st.info("Enter a search term first.")
            else:
                matches = movies[movies['title'].str.contains(title_query, case=False, na=False)]
                if matches.empty:
                    st.write('No matches found.')
                else:
           
                    for _, row in matches.iterrows():
                        st.write(f"🎬 **{row['title']}** — {row['genres']}")
                        if 'description' in row and pd.notna(row.get('description')):
                            st.write(row['description'])

                        if 'user' in st.session_state:
                            form_key = f"rate_form_{row['movieId']}"
                            with st.form(key=form_key):
                         
                                default_val = 0.0
                                ur = st.session_state.get('user_ratings', {})
                                try:
                                    if int(row['movieId']) in ur:
                                        default_val = float(ur[int(row['movieId'])])
                                except Exception:
                                  
                                    if str(row['movieId']) in ur:
                                        default_val = float(ur[str(row['movieId'])])

                                rating = st.slider(f"Rate {row['title']}", 0.0, 5.0, default_val, 0.5, key=f"slider_{row['movieId']}")
                                submitted = st.form_submit_button('💾 Save rating')
                                if submitted:
                                    
                                    try:
                                        db.add_rating(st.session_state['user']['id'], int(row['movieId']), float(rating))
                                    except Exception:
                       
                                        db.add_rating(st.session_state['user']['id'], row['movieId'], float(rating))

                              
                                    st.session_state['user_ratings'] = fetch_user_ratings_from_db(st.session_state['user']['id'])
                                    st.success(f"✅ Rating for '{row['title']}' saved: {rating} ⭐")
                             

                        else:
                            st.info('🔐 Login to rate movies.')

    with col2:
        st.subheader('⚡ Quick actions')

        if st.button('Recommend for me (hybrid)'):
            if 'user' in st.session_state:
              
                recs = rec.collaborative_recommend(st.session_state['user']['id'], top_n=6)
                if recs:
                    st.write('🎯 Recommendations for you:')
                    for r in recs:
                        st.write(f"**{r['title']}** — score: {r['score']:.3f}")
                else:
                    st.info('📊 Not enough data for collaborative recommendations. Try rating a few movies.')
            else:
                st.info('🔐 Login to get personalized recommendations.')

        st.markdown('---')
        st.subheader('📂 Dataset sample')
        st.dataframe(movies[['movieId', 'title', 'genres']].head(10), use_container_width=True)

        st.markdown('---')
        st.subheader('⭐ Your ratings')
        if 'user' in st.session_state:
            ur = st.session_state.get('user_ratings', {})
            if ur:
               
                rows = []
                for mid, val in ur.items():
                    title = find_title_by_movieid(movies, mid) or find_title_by_movieid(movies, str(mid))
                    if not title:
                        title = f"Movie {mid}"
                    rows.append((title, val))
          
                rows.sort(key=lambda x: x[0])
                for title, val in rows:
                    st.write(f"🎞 **{title}** — {val} ⭐")
            else:
                st.info('You haven’t rated any movies yet.')
        else:
            st.info('🔐 Login to see your ratings.')

    st.markdown('---')
    st.caption('Built with ❤️ — Streamlit + Transformers + TF-IDF + SQLite')

if __name__ == '__main__':
    main()
