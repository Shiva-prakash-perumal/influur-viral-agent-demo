with source as (
    select
        post_id,
        influencer_id,
        platform,
        posted_at::timestamp,
        caption,
        views::bigint,
        likes::bigint,
        comments::bigint,
        shares::bigint,
        audio_type,
        campaign_tag
    from {{ source('raw', 'raw_posts') }}
)

select * from source
