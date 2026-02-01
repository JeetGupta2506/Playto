from rest_framework import serializers
from .models import Post, Comment, Like, KarmaTransaction


class CommentSerializer(serializers.ModelSerializer):
    """
    Recursive serializer for nested comments.
    Uses prefetch optimization to avoid N+1 queries.
    """
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'parent', 'author', 'content', 'like_count', 
                  'created_at', 'depth', 'replies']
        read_only_fields = ['like_count', 'depth', 'created_at']
    
    def get_replies(self, obj):
        """
        Get nested replies from prefetched data.
        This avoids recursive database queries.
        """
        # Check if replies are prefetched
        if hasattr(obj, '_prefetched_replies'):
            replies = obj._prefetched_replies
        else:
            replies = obj.replies.all()
        
        return CommentSerializer(replies, many=True, context=self.context).data


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for posts with optional comment tree inclusion.
    """
    comments = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'like_count', 'created_at', 
                  'updated_at', 'comments', 'comment_count']
        read_only_fields = ['like_count', 'created_at', 'updated_at']
    
    def get_comments(self, obj):
        """
        Get comment tree efficiently using path-based ordering.
        Returns only root comments with nested replies.
        """
        # Only include comments if requested
        if not self.context.get('include_comments', False):
            return []
        
        # Get all comments for this post (prefetched)
        if hasattr(obj, '_prefetched_comments'):
            all_comments = list(obj._prefetched_comments)
        else:
            all_comments = list(obj.comments.all())
        
        # Build tree structure
        comment_map = {comment.id: comment for comment in all_comments}
        
        # Attach replies to their parents
        for comment in all_comments:
            comment._prefetched_replies = []
        
        for comment in all_comments:
            if comment.parent_id and comment.parent_id in comment_map:
                parent = comment_map[comment.parent_id]
                parent._prefetched_replies.append(comment)
        
        # Get root comments (no parent)
        root_comments = [c for c in all_comments if c.parent_id is None]
        
        return CommentSerializer(root_comments, many=True, context=self.context).data
    
    def get_comment_count(self, obj):
        """Get total comment count."""
        if hasattr(obj, 'comment_count_annotated'):
            return obj.comment_count_annotated
        return obj.comments.count()


class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for like actions.
    """
    class Meta:
        model = Like
        fields = ['id', 'user', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['created_at']


class LeaderboardSerializer(serializers.Serializer):
    """
    Serializer for leaderboard entries.
    """
    user = serializers.CharField()
    karma = serializers.IntegerField()
    rank = serializers.IntegerField()
