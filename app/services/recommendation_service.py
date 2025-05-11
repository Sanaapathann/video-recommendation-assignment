import asyncio
from typing import Dict, List, Any, Optional
from fastapi import HTTPException, Depends
import random
from collections import Counter
import numpy as np
from sqlalchemy.orm import Session
from app.services.empowerverse_api import EmpowerVerseApiService
from app.core.config import settings
from app.db.database import get_db
from app.models.user_interaction import UserInteraction
import logging
from datetime import datetime, timedelta
from dateutil import parser

# Configure logging
logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self, db: Session = None):
        self.api_service = EmpowerVerseApiService()
        self.cache = {}
        self.cache_ttl = settings.CACHE_TTL
        self.db = db
        
    async def get_user_interactions(self, username: str, db: Session = None) -> Dict[str, Any]:
        """Get all user interactions (views, likes, inspires, ratings) directly from API"""
        logger.info(f"Getting user by username: {username}")
        try:
            # IMPORTANT: Set mock and fallback to false to ensure we're getting real API data
            original_mock = self.api_service.use_mock
            original_fallback = self.api_service.use_fallback
            
            # Force real API usage first
            self.api_service.use_mock = False
            self.api_service.use_fallback = False
            
            # Get the user from the real API
            try:
                user = await self.api_service.get_user_by_username(username)
                logger.info(f"Found real user: {user.get('id')}")
            except Exception as e:
                logger.warning(f"Error fetching real user data: {str(e)}")
                # Restore original settings if real API fetch fails
                self.api_service.use_mock = original_mock
                self.api_service.use_fallback = original_fallback
                user = await self.api_service.get_user_by_username(username)
            
            # Check if user was found
            if not user:
                logger.error(f"User not found: {username}")
                raise HTTPException(status_code=404, detail=f"User '{username}' not found")
                
            logger.info(f"Found user: {user.get('id')}")
            user_id = user.get("id")
            
            # Check if user ID is valid
            if not user_id:
                logger.error(f"User has no ID: {username}")
                raise HTTPException(status_code=500, detail=f"User '{username}' has no ID")
            
            # Initialize empty interactions in case DB or API fetch fails
            viewed_posts = []
            liked_posts = []
            inspired_posts = []
            rated_posts = []
            
            # Fetch all interaction data in parallel from API - still using real API
            try:
                logger.info("Fetching user interactions data from API")
                viewed_task = self.api_service.get_viewed_posts(page_size=1000)
                liked_task = self.api_service.get_liked_posts(page_size=1000)
                inspired_task = self.api_service.get_inspired_posts(page_size=1000)
                rated_task = self.api_service.get_rated_posts(page_size=1000)
                
                viewed_data, liked_data, inspired_data, rated_data = await asyncio.gather(
                    viewed_task, liked_task, inspired_task, rated_task
                )
                
                # Debug log the data
                logger.debug(f"Viewed Data: {viewed_data}")
                logger.debug(f"Liked Data: {liked_data}")
                logger.debug(f"Inspired Data: {inspired_data}")
                logger.debug(f"Rated Data: {rated_data}")
                
                # Filter interactions by user_id
                viewed_posts = self._filter_user_interactions(viewed_data, user_id)
                liked_posts = self._filter_user_interactions(liked_data, user_id)
                inspired_posts = self._filter_user_interactions(inspired_data, user_id)
                rated_posts = self._filter_user_interactions(rated_data, user_id)
                
                logger.info(f"User interactions for {username} (user_id={user_id}): {len(viewed_posts)} views, {len(liked_posts)} likes, {len(inspired_posts)} inspires, {len(rated_posts)} ratings")
                
                # Log interaction details for debugging
                if viewed_posts:
                    logger.debug(f"Sample viewed post: {viewed_posts[0]}")
                if liked_posts:
                    logger.debug(f"Sample liked post: {liked_posts[0]}")
                    
            except Exception as e:
                logger.error(f"Error fetching interactions from API: {str(e)}", exc_info=True)
                # Continue with empty interactions lists
            
            # Restore original settings
            self.api_service.use_mock = original_mock
            self.api_service.use_fallback = original_fallback
            
            return {
                "user": user,
                "viewed_posts": viewed_posts,
                "liked_posts": liked_posts,
                "inspired_posts": inspired_posts,
                "rated_posts": rated_posts
            }
        except HTTPException as e:
            # Re-raise HTTP exceptions (including 404 for user not found)
            logger.error(f"HTTP exception in get_user_interactions: {e.detail}")
            raise
        except Exception as e:
            error_detail = f"Error getting user interactions: {str(e)}"
            logger.error(error_detail, exc_info=True)
            raise HTTPException(status_code=500, detail=error_detail)
    
    def _store_interactions_in_db(self, db: Session, user_id: str, interactions: List[Dict[str, Any]], interaction_type: str):
        """Store interactions in database"""
        # First, delete existing interactions of this type
        db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id,
            UserInteraction.interaction_type == interaction_type
        ).delete()
        
        # Add new interactions
        for interaction in interactions:
            db_interaction = UserInteraction(
                user_id=user_id,
                post_id=interaction.get("post_id"),
                interaction_type=interaction_type,
                rating_value=interaction.get("rating_value") if interaction_type == "rate" else None
            )
            db.add(db_interaction)
        
        db.commit()
        
    def _filter_user_interactions(self, interaction_data: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
        """Filter interaction data by user_id"""
        interactions = interaction_data.get("data", [])
        logger.debug(f"Filtering {len(interactions)} interactions for user_id={user_id}")
        
        # Debug log the structure of interactions for diagnosis
        if interactions and len(interactions) > 0:
            logger.debug(f"Sample interaction structure: {interactions[0]}")
            available_user_ids = set(i.get("user_id") for i in interactions if i.get("user_id"))
            logger.debug(f"Available user_ids in interactions: {available_user_ids}")
            
        # Filter interactions by exact user_id match
        filtered = [i for i in interactions if i.get("user_id") == user_id]
        logger.debug(f"Found {len(filtered)} interactions matching user_id={user_id}")
        
        return filtered
        
    async def get_personalized_feed(self, username: str, project_code: Optional[str] = None, page: int = 1, page_size: int = 20, db: Session = None) -> Dict[str, Any]:
        """Generate personalized feed for a user, optionally filtered by project_code"""
        logger.info(f"Generating personalized feed for {username}, project_code={project_code}")
        cache_key = f"feed_{username}_{project_code}_{page}_{page_size}"
        
        # Check cache
        if cache_key in self.cache:
            logger.info(f"Using cached result for {cache_key}")
            return self.cache[cache_key]
            
        try:
            # Get user interactions
            logger.info("Getting user interactions")
            user_data = await self.get_user_interactions(username, db)
            
            if not user_data or "user" not in user_data:
                logger.error(f"Failed to get user data for {username}")
                raise HTTPException(status_code=404, detail=f"User '{username}' not found")
                
            user = user_data["user"]
            
            # Get all posts
            logger.info("Getting all posts")
            all_posts_data = await self.api_service.get_all_posts(page_size=1000)
            all_posts = all_posts_data.get("data", [])
            logger.info(f"Got {len(all_posts)} posts")
            
            # Check if we got any posts
            if not all_posts:
                logger.warning("No posts found in the API response")
                return {
                    "status": "success",
                    "post": []
                }
            
            # Filter by project_code if specified
            if project_code:
                logger.info(f"Filtering by project_code {project_code}")
                all_posts = [p for p in all_posts if p.get("project_code") == project_code]
                logger.info(f"After filtering: {len(all_posts)} posts")
                
            # Calculate content-based and collaborative filtering scores
            if len(user_data.get("viewed_posts", [])) > 0 or len(user_data.get("liked_posts", [])) > 0:
                # Generate recommendations based on user history
                logger.info("Generating recommendations based on user history")
                recommendations = await self._generate_recommendations(user_data, all_posts)
            else:
                # Cold start: recommend popular content or random selection
                logger.info("Cold start: using popularity-based recommendations")
                recommendations = await self._handle_cold_start(user, all_posts, project_code)
                
            # Paginate results
            total_items = len(recommendations)
            total_pages = max(1, (total_items + page_size - 1) // page_size)
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_items)
            
            logger.info(f"Pagination: page {page}/{total_pages}, items {start_idx+1}-{end_idx}/{total_items}")
            
            paginated_posts = recommendations[start_idx:end_idx]
            
            # Format posts according to the required schema
            formatted_posts = []
            for post in paginated_posts:
                try:
                    # Create BaseToken
                    base_token = {
                        "address": post.get("contract_address", ""),
                        "name": post.get("token_name", ""),
                        "symbol": post.get("token_symbol", ""),
                        "image_url": post.get("token_image_url", "")
                    }
                    
                    # Create Owner
                    owner = {
                        "first_name": post.get("user", {}).get("first_name", "Unknown"),
                        "last_name": post.get("user", {}).get("last_name", "User"),
                        "name": post.get("user", {}).get("name", "Unknown User"),
                        "username": post.get("user", {}).get("username", "unknown"),
                        "picture_url": post.get("user", {}).get("profile_photo_url", "https://assets.socialverseapp.com/profile/default.png"),
                        "user_type": post.get("user", {}).get("user_type"),
                        "has_evm_wallet": post.get("user", {}).get("has_evm_wallet", False),
                        "has_solana_wallet": post.get("user", {}).get("has_solana_wallet", False)
                    }
                    
                    # Create Category
                    category = {
                        "id": int(post.get("category_id", 13)),
                        "name": post.get("category_name", "Flic"),
                        "count": post.get("category_count", 125),
                        "description": post.get("category_description", "Where Creativity Meets Opportunity"),
                        "image_url": post.get("category_image_url", "https://socialverse-assets.s3.us-east-1.amazonaws.com/categories/NEW_COLOR.png")
                    }
                    
                    # Create Topic Owner
                    topic_owner = {
                        "first_name": post.get("topic_owner_first_name", "Shivam"),
                        "last_name": post.get("topic_owner_last_name", "Flic"),
                        "name": post.get("topic_owner_name", "Shivam Flic"),
                        "username": post.get("topic_owner_username", "random"),
                        "profile_url": post.get("topic_owner_profile_url", "https://assets.socialverseapp.com/profile/random.png"),
                        "user_type": post.get("topic_owner_user_type", "hirer"),
                        "has_evm_wallet": post.get("topic_owner_has_evm_wallet", False),
                        "has_solana_wallet": post.get("topic_owner_has_solana_wallet", False)
                    }
                    
                    # Create Topic
                    topic = {
                        "id": int(post.get("topic_id", 1)),
                        "name": post.get("topic_name", "Social Media"),
                        "description": post.get("topic_description", "Short form content making and editing."),
                        "image_url": post.get("topic_image_url", "https://ui-avatars.com/api/?size=300&name=Social%20Media&color=fff&background=random"),
                        "slug": post.get("topic_slug", "b9f5413f04ec58e47874"),
                        "is_public": post.get("topic_is_public", True),
                        "project_code": post.get("project_code", "flic"),
                        "posts_count": post.get("topic_posts_count", 18),
                        "language": post.get("topic_language"),
                        "created_at": post.get("topic_created_at", "2025-02-15 15:02:41"),
                        "owner": topic_owner
                    }
                    
                    # Format the post
                    formatted_post = {
                        "id": int(post.get("id", 0)),
                        "owner": owner,
                        "category": category,
                        "topic": topic,
                        "title": post.get("title", "Untitled"),
                        "is_available_in_public_feed": post.get("is_available_in_public_feed", True),
                        "is_locked": post.get("is_locked", False),
                        "slug": post.get("slug", f"{hash(post.get('id', ''))}"),
                        "upvoted": post.get("upvoted", False),
                        "bookmarked": post.get("bookmarked", False),
                        "following": post.get("following", False),
                        "identifier": post.get("identifier", f"ID{hash(post.get('id', ''))}"[:7]),
                        "comment_count": int(post.get("comment_count", 0)),
                        "upvote_count": int(post.get("likes_count", 0)),
                        "view_count": int(post.get("views_count", 0)),
                        "exit_count": int(post.get("exit_count", 0)),
                        "rating_count": int(post.get("rating_count", 0)),
                        "average_rating": int(post.get("ratings_average", 0) * 20) if post.get("ratings_average") else 0,  # Convert 0-5 to 0-100
                        "share_count": int(post.get("share_count", 0)),
                        "bookmark_count": int(post.get("bookmark_count", 0)),
                        "video_link": post.get("video_url", ""),
                        "thumbnail_url": post.get("thumbnail_url", ""),
                        "gif_thumbnail_url": post.get("gif_thumbnail_url", post.get("thumbnail_url", "")),
                        "contract_address": post.get("contract_address", ""),
                        "chain_id": post.get("chain_id", ""),
                        "chart_url": post.get("chart_url", ""),
                        "baseToken": base_token,
                        "created_at": int(post.get("created_at_timestamp", datetime.now().timestamp() * 1000)),  # Convert to milliseconds
                        "tags": post.get("tags", [])
                    }
                    
                    formatted_posts.append(formatted_post)
                except Exception as e:
                    logger.error(f"Error formatting post {post.get('id')}: {str(e)}")
                    continue
            
            result = {
                "status": "success",
                "post": formatted_posts
            }
            
            # Cache result
            self.cache[cache_key] = result
            
            return result
            
        except HTTPException as e:
            # Re-raise HTTP exceptions
            logger.error(f"HTTP exception in get_personalized_feed: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate personalized feed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to generate personalized feed: {str(e)}")
            
    async def _generate_recommendations(self, user_data: Dict[str, Any], all_posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on user history with advanced ML/DL-like features"""
        # Extract post IDs the user has already interacted with
        viewed_ids = {p.get("post_id") for p in user_data.get("viewed_posts", [])}
        liked_ids = {p.get("post_id") for p in user_data.get("liked_posts", [])}
        inspired_ids = {p.get("post_id") for p in user_data.get("inspired_posts", [])}
        rated_posts = user_data.get("rated_posts", [])
        
        # Get high-rated posts (rating >= 4)
        # Fix for NoneType error - ensure rating_value is not None
        high_rated_ids = {p.get("post_id") for p in rated_posts 
                         if p.get("rating_value") is not None and float(p.get("rating_value", 0)) >= 4}
        
        # Combine all interacted posts
        all_interacted_ids = viewed_ids.union(liked_ids).union(inspired_ids).union({p.get("post_id") for p in rated_posts})
        
        # Get posts user hasn't seen yet (filter out already viewed posts)
        unseen_posts = [p for p in all_posts if p.get("id") not in viewed_ids]
        
        # If no posts available to recommend, return empty list
        if not unseen_posts:
            logger.warning("No unseen posts available for recommendation")
            return []
        
        # Get top creators (users whose content the user likes)
        liked_creator_ids = [p.get("user_id") for p in user_data.get("liked_posts", [])]
        inspired_creator_ids = [p.get("user_id") for p in user_data.get("inspired_posts", [])]
        high_rated_creator_ids = [p.get("user_id") for p in rated_posts 
                                 if p.get("rating_value") is not None and float(p.get("rating_value", 0)) >= 4]
        
        # Combine and count occurrences
        all_preferred_creators = liked_creator_ids + inspired_creator_ids + high_rated_creator_ids
        creator_counts = Counter(all_preferred_creators)
        top_creators = [creator_id for creator_id, count in creator_counts.most_common(5)]
        
        # Collect user interests from interactions
        user_interests = set()
        user_moods = Counter()
        user_tags = Counter()
        
        # Gather information about categories, tags, and moods from liked and high-rated posts
        for post_id in liked_ids.union(high_rated_ids):
            post = next((p for p in all_posts if p.get("id") == post_id), None)
            if post:
                # Get categories
                if post.get("categories"):
                    user_interests.update(post.get("categories", []))
                
                # Get tags 
                if post.get("tags"):
                    user_tags.update(post.get("tags", []))
                
                # Get mood
                if post.get("mood"):
                    user_moods[post.get("mood")] += 1
        
        # Get top categories/interests from user data
        if not user_interests:
            # If no interests found from posts, try to get them from user profile
            if user_data.get("user", {}).get("interests"):
                user_interests = set(user_data.get("user", {}).get("interests", []))
        
        # Get project codes/categories for content-based filtering
        liked_categories = [p.get("project_code") for p in all_posts if p.get("id") in liked_ids and p.get("project_code")]
        category_counts = Counter(liked_categories)
        top_categories = [category for category, count in category_counts.most_common(3)]
        
        # Find the most frequent mood if available
        preferred_mood = user_moods.most_common(1)[0][0] if user_moods else None
        
        # Score each unseen post
        scored_posts = []
        for post in unseen_posts:
            score = 0
            
            # Content from preferred creators gets a boost
            if post.get("user_id") in top_creators and creator_counts:
                # Avoid division by zero or None by using a default max count of 1
                max_count = max(creator_counts.values()) if creator_counts else 1
                score += 30 * (creator_counts.get(post.get("user_id"), 0) / max_count)
            
            # Content in preferred categories gets a boost
            if post.get("project_code") in top_categories and category_counts:
                max_count = max(category_counts.values()) if category_counts else 1
                score += 20 * (category_counts.get(post.get("project_code"), 0) / max_count)
            
            # Content matching user interests gets a boost
            if post.get("categories"):
                matching_categories = user_interests.intersection(set(post.get("categories", [])))
                category_match_score = len(matching_categories) / len(post.get("categories", [])) if post.get("categories") else 0
                score += 25 * category_match_score
                
            # Content with matching tags gets a boost
            if post.get("tags") and user_tags:
                matching_tags = set(post.get("tags", [])).intersection(set(user_tags.keys()))
                if matching_tags:
                    tag_match_score = sum(user_tags[tag] for tag in matching_tags) / sum(user_tags.values())
                    score += 15 * tag_match_score
            
            # Content with matching mood gets a boost
            if preferred_mood and post.get("mood") == preferred_mood:
                score += 15
            
            # Popular content gets a boost - handle potential None values
            views_count = post.get("views_count") or 0
            likes_count = post.get("likes_count") or 0
            inspires_count = post.get("inspires_count") or 0
            ratings_average = post.get("ratings_average") or 0
            
            score += min(views_count / 100, 10)
            score += min(likes_count / 10, 20)
            score += min(inspires_count / 5, 20)
            score += min(ratings_average * 5, 20)
            
            # Add recency boost (newer content)
            if post.get("created_at"):
                try:
                    # Parse the datetime and calculate days since creation
                    import datetime as dt
                    from dateutil import parser
                    created_date = parser.parse(post.get("created_at"))
                    days_old = (dt.datetime.now(dt.timezone.utc) - created_date).days
                    recency_score = max(0, 10 - min(days_old, 10))  # 0-10 score based on recency
                    score += recency_score
                except (ValueError, ImportError):
                    # If date parsing fails, skip this boost
                    pass
            
            # Add some randomness for exploration
            score += random.uniform(0, 10)
            
            scored_posts.append((post, score))
            
        # Sort by score (descending)
        scored_posts.sort(key=lambda x: x[1], reverse=True)
        
        # Return sorted posts
        return [post for post, score in scored_posts]
        
    async def _handle_cold_start(self, user: Dict[str, Any], all_posts: List[Dict[str, Any]], project_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Handle cold start problem (new users with no history)"""
        # If there are no posts, return empty list
        if not all_posts:
            logger.warning("No posts available for cold start recommendations")
            return []
            
        # Start with popular content
        popular_posts = sorted(all_posts, key=lambda p: (
            (p.get("views_count") or 0) + 
            (p.get("likes_count") or 0) * 5 + 
            (p.get("inspires_count") or 0) * 10 + 
            (p.get("ratings_average") or 0) * 20
        ), reverse=True)
        
        # Ensure diversity by not showing all from the same creator
        creator_seen = set()
        diverse_posts = []
        
        for post in popular_posts:
            creator_id = post.get("user_id")
            if creator_id and (creator_id not in creator_seen or len(creator_seen) > 10):
                diverse_posts.append(post)
                creator_seen.add(creator_id)
                
        # Add some random posts for exploration
        if len(diverse_posts) < len(all_posts):
            remaining_posts = [p for p in all_posts if p not in diverse_posts]
            # Make sure we don't try to sample more posts than available
            sample_count = min(10, len(remaining_posts))
            if sample_count > 0:
                random_posts = random.sample(remaining_posts, sample_count)
                diverse_posts.extend(random_posts)
            
        return diverse_posts 