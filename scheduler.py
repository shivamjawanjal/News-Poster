from apscheduler.schedulers.background import BackgroundScheduler
from news_fetcher import fetch_news
from storage import *
from ai_gemini import analyze_news
from post_generator import create_post

def job():
    news = fetch_news()
    posted = get_posted_ids()
    queue = get_queue()

    fresh = [n for n in news if n["article_id"] not in posted]

    if len(fresh) > 5:
        queue.extend(fresh[5:])
        fresh = fresh[:5]

    if not fresh and queue:
        fresh = queue[:5]
        queue = queue[5:]

    for n in fresh:
        ai_text = analyze_news(n)
        create_post(ai_text)
        posted.append(n["article_id"])

    save_posted_ids(posted)
    save_queue(queue)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, "interval", minutes=30)
    scheduler.start()
