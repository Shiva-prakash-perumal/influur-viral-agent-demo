select
    p.post_id,
    p.influencer_id,
    p.platform,
    date_trunc('day', p.posted_at) as post_date,
    p.views,
    p.likes,
    p.comments,
    p.shares,
    case
        when p.views = 0 then 0
        else (p.likes + p.comments + p.shares)::float / p.views
    end as engagement_rate,
    p.audio_type,
    p.campaign_tag
from {{ ref('stg_posts') }} p
