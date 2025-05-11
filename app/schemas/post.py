from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

class BaseTokenModel(BaseModel):
    address: str = ""
    name: str = ""
    symbol: str = ""
    image_url: str = ""

class TopicOwnerModel(BaseModel):
    first_name: str
    last_name: str
    name: str
    username: str
    profile_url: str
    user_type: Optional[str] = None
    has_evm_wallet: Optional[bool] = False
    has_solana_wallet: Optional[bool] = False

class TopicModel(BaseModel):
    id: int
    name: str
    description: str
    image_url: str
    slug: str
    is_public: bool
    project_code: str
    posts_count: int
    language: Optional[str] = None
    created_at: str
    owner: TopicOwnerModel

class CategoryModel(BaseModel):
    id: int
    name: str
    count: int
    description: str
    image_url: str

class OwnerModel(BaseModel):
    first_name: str
    last_name: str
    name: str
    username: str
    picture_url: str
    user_type: Optional[str] = None
    has_evm_wallet: bool = False
    has_solana_wallet: bool = False

class PostModel(BaseModel):
    id: int
    owner: OwnerModel
    category: CategoryModel
    topic: TopicModel
    title: str
    is_available_in_public_feed: bool = True
    is_locked: bool = False
    slug: str
    upvoted: bool = False
    bookmarked: bool = False
    following: bool = False
    identifier: str
    comment_count: int = 0
    upvote_count: int = 0
    view_count: int = 0
    exit_count: int = 0
    rating_count: int = 0
    average_rating: int = 0
    share_count: int = 0
    bookmark_count: int = 0
    video_link: str
    thumbnail_url: str
    gif_thumbnail_url: str
    contract_address: str = ""
    chain_id: str = ""
    chart_url: str = ""
    baseToken: BaseTokenModel
    created_at: int  # Timestamp in milliseconds
    tags: List[str] = []

class RecommendationResponse(BaseModel):
    status: str = "success"
    post: List[PostModel] = []

class FeedRequest(BaseModel):
    username: str
    project_code: Optional[str] = None
    page: int = 1
    page_size: int = 20 