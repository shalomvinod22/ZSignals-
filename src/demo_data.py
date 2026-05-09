"""Demo data for Zintlr Pulse.

Provides curated example posts for testing and demos.
Mix of intent levels, platforms, and geographies.
"""

from datetime import datetime, timedelta


def get_demo_posts() -> list[dict]:
    """Return list of 12 curated demo posts.
    
    Returns:
        List of lead dicts matching scraper output schema.
    """
    now = datetime.utcnow()
    
    posts = [
        # HIGH INTENT (score 5) — 3 posts
        {
            "platform": "Reddit",
            "source_url": "https://reddit.com/r/sales/comments/demo1",
            "username": "sdr_burnedout_blr",
            "date": (now - timedelta(hours=2)).isoformat() + "Z",
            "content": "42% of my emails to India bounced. Wasted half my month's credits. Looking for alternatives that work for APAC. Apollo accuracy is just 73% here.",
            "post_id": "reddit_demo_high1",
            "has_tier1_keyword": True,
            "has_tier2_keyword": True,
            "raw_score": 45,
            "subreddit": "sales",
        },
        {
            "platform": "G2",
            "source_url": "https://www.g2.com/products/zoominfo/reviews",
            "username": "Priya_Sharma",
            "date": (now - timedelta(days=1)).isoformat() + "Z",
            "content": "We switched to Zintlr after 6 months of ZoomInfo. Our India prospect list accuracy went from 68% to 97%. Best decision for our BDR team.",
            "post_id": "g2_demo_high2",
            "has_tier1_keyword": True,
            "has_tier2_keyword": True,
            "raw_score": 1.0,
            "product_slug": "zoominfo",
        },
        {
            "platform": "Reddit (comment)",
            "source_url": "https://reddit.com/r/IndianStartups/comments/demo3",
            "username": "founder_bengaluru",
            "date": (now - timedelta(hours=6)).isoformat() + "Z",
            "content": "Lusha kept giving me wrong mobile numbers for APAC. Terrible for India outreach. Switched to Zintlr and haven't looked back. 98% accuracy on verified emails.",
            "post_id": "reddit_demo_high3",
            "has_tier1_keyword": True,
            "has_tier2_keyword": True,
            "raw_score": 62,
            "subreddit": "IndianStartups",
        },
        # MEDIUM INTENT (score 3-4) — 4 posts
        {
            "platform": "Reddit",
            "source_url": "https://reddit.com/r/SalesOperations/comments/demo4",
            "username": "ops_manager_sf",
            "date": (now - timedelta(days=2)).isoformat() + "Z",
            "content": "Evaluating alternatives to Apollo. Our bounce rate is getting worse. Any recommendations for tools that focus on data quality?",
            "post_id": "reddit_demo_med1",
            "has_tier1_keyword": True,
            "has_tier2_keyword": True,
            "raw_score": 28,
            "subreddit": "SalesOperations",
        },
        {
            "platform": "Hacker News",
            "source_url": "https://news.ycombinator.com/item?id=demo5",
            "username": "techfodder",
            "date": (now - timedelta(days=3)).isoformat() + "Z",
            "content": "Anyone using Cognism or an alternative? Looking for a b2b data provider that doesn't break the bank and actually delivers accuracy.",
            "post_id": "hn_demo_med2",
            "has_tier1_keyword": True,
            "has_tier2_keyword": False,
            "raw_score": 15,
        },
        {
            "platform": "Reddit",
            "source_url": "https://reddit.com/r/coldemail/comments/demo6",
            "username": "growth_hacker",
            "date": (now - timedelta(hours=12)).isoformat() + "Z",
            "content": "Our outbound stack: Apollo, Instantly, Clay. Apollo data quality has been a bottleneck lately. Looking for comparisons with Zintlr or Clearbit.",
            "post_id": "reddit_demo_med3",
            "has_tier1_keyword": True,
            "has_tier2_keyword": False,
            "raw_score": 33,
            "subreddit": "coldemail",
        },
        {
            "platform": "Reddit",
            "source_url": "https://reddit.com/r/LeadGeneration/comments/demo7",
            "username": "bdr_frustrated",
            "date": (now - timedelta(days=1)).isoformat() + "Z",
            "content": "Sick of Apollo's email bounces. Does anyone else hate dealing with this? Thinking of switching but not sure what's out there.",
            "post_id": "reddit_demo_med4",
            "has_tier1_keyword": True,
            "has_tier2_keyword": True,
            "raw_score": 19,
            "subreddit": "LeadGeneration",
        },
        # LOW INTENT (score 1-2) — 2 posts
        {
            "platform": "Reddit",
            "source_url": "https://reddit.com/r/SaaS/comments/demo8",
            "username": "random_redditor",
            "date": (now - timedelta(days=5)).isoformat() + "Z",
            "content": "We're hiring our first SDR and looking to expand the sales team. Any tools you recommend for lead research?",
            "post_id": "reddit_demo_low1",
            "has_tier1_keyword": False,
            "has_tier2_keyword": False,
            "raw_score": 7,
            "subreddit": "SaaS",
        },
        {
            "platform": "Reddit",
            "source_url": "https://reddit.com/r/sales/comments/demo9",
            "username": "skeptic_sales",
            "date": (now - timedelta(days=4)).isoformat() + "Z",
            "content": "Had a decent experience with Apollo but not complaining. Data is accurate enough for US. Not sure about international.",
            "post_id": "reddit_demo_low2",
            "has_tier1_keyword": True,
            "has_tier2_keyword": False,
            "raw_score": 4,
            "subreddit": "sales",
        },
        # DISQUALIFIER — 2 posts
        {
            "platform": "Reddit",
            "source_url": "https://reddit.com/r/sales/comments/demo10",
            "username": "apollo_employee",
            "date": (now - timedelta(days=2)).isoformat() + "Z",
            "content": "I work at Apollo. Most of those complaints are user error. Our APAC data is actually the best on the market.",
            "post_id": "reddit_demo_dq1",
            "has_tier1_keyword": True,
            "has_tier2_keyword": False,
            "raw_score": 2,
            "subreddit": "sales",
        },
        {
            "platform": "Reddit",
            "source_url": "https://reddit.com/r/LeadGeneration/comments/demo11",
            "username": "job_recruiter",
            "date": (now - timedelta(days=1)).isoformat() + "Z",
            "content": "Hiring: SDR for Series B startup. Competitive salary. Must have 2+ years outbound experience. Apply here.",
            "post_id": "reddit_demo_dq2",
            "has_tier1_keyword": False,
            "has_tier2_keyword": False,
            "raw_score": 1,
            "subreddit": "LeadGeneration",
        },
        # MIXED SIGNAL — 1 post
        {
            "platform": "Reddit (comment)",
            "source_url": "https://reddit.com/r/developersIndia/comments/demo12",
            "username": "delhi_startup_dev",
            "date": (now - timedelta(hours=8)).isoformat() + "Z",
            "content": "We're a Series A fintech in Delhi looking for India-verified contact data. Apollo bounces are killing us. Our new VP Sales is exploring alternatives.",
            "post_id": "reddit_demo_mixed1",
            "has_tier1_keyword": True,
            "has_tier2_keyword": True,
            "raw_score": 22,
            "subreddit": "developersIndia",
        },
    ]
    
    return posts
