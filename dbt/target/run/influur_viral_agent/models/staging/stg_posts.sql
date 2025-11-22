
  create view "influur_demo"."public_staging"."stg_posts__dbt_tmp"
    
    
  as (
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
    from "influur_demo"."public"."raw_posts"
)

select * from source
  );