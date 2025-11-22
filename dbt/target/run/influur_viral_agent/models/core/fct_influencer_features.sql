
  create view "influur_demo"."public_core"."fct_influencer_features__dbt_tmp"
    
    
  as (
    with perf as (
    select
        influencer_id,
        avg(views) as avg_views_last_n_posts,
        avg(engagement_rate) as avg_engagement_last_n_posts,
        avg(shares)::float as avg_shares,
        count(*) as post_count
    from "influur_demo"."public_core"."fact_post_performance"
    where post_date >= current_date - interval '90 days'
    group by influencer_id
),

base as (
    select
        i.influencer_id,
        i.handle,
        i.platform,
        i.follower_count,
        i.avg_views as historical_avg_views,
        i.engagement_rate as historical_engagement_rate,
        i.country,
        i.language,
        i.category,
        i.content_style,
        i.cost_per_post,
        i.age_bracket,
        coalesce(p.avg_views_last_n_posts, i.avg_views) as recent_avg_views,
        coalesce(p.avg_engagement_last_n_posts, i.engagement_rate) as recent_engagement_rate,
        coalesce(p.post_count, 0) as post_count_last_90d
    from "influur_demo"."public_staging"."stg_influencers" i
    left join perf p on i.influencer_id = p.influencer_id
)

select * from base
  );