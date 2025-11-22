
  create view "influur_demo"."public_staging"."stg_influencers__dbt_tmp"
    
    
  as (
    with source as (
    select
        influencer_id,
        handle,
        platform,
        follower_count::bigint,
        avg_views::bigint,
        engagement_rate::float,
        country,
        language,
        category,
        content_style,
        cost_per_post::numeric,
        age_bracket
    from "influur_demo"."public"."raw_influencers"
)

select * from source
  );