with features as (
    select * from "influur_demo"."public_core"."fct_influencer_features"
),

scored as (
    select
        influencer_id,
        handle,
        platform,
        follower_count,
        country,
        language,
        category,
        content_style,
        cost_per_post,
        age_bracket,
        recent_avg_views,
        recent_engagement_rate,
        post_count_last_90d,
        (
            0.4 * (log(greatest(recent_avg_views, 1))) +
            0.4 * (recent_engagement_rate * 100) +
            0.2 * log(greatest(post_count_last_90d + 1, 1))
        ) as virality_score
    from features
)

select * from scored