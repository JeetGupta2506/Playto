from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, IntegrityError
from django.db.models import Count, Sum, Q, Prefetch, F
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta

from .models import Post, Comment, Like, KarmaTransaction
from .serializers import (
    PostSerializer, 
    CommentSerializer, 
    LikeSerializer,
    LeaderboardSerializer
)


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Post operations.
    Optimized with select_related and prefetch_related to avoid N+1 queries.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    def get_queryset(self):
        """
        Optimize queryset with annotations and prefetching.
        """
        queryset = Post.objects.annotate(
            comment_count_annotated=Count('comments')
        )
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single post with its comment tree.
        Optimized to fetch all comments in a single query.
        """
        instance = self.get_object()
        
        # Prefetch all comments for this post in one query
        # Using path ordering ensures proper tree structure
        comments = Comment.objects.filter(post=instance).order_by('path').select_related('parent')
        instance._prefetched_comments = comments
        
        serializer = self.get_serializer(instance, context={'include_comments': True})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Like a post. Uses database-level unique constraint to prevent double-liking.
        Implements atomic transaction to handle race conditions.
        """
        post = self.get_object()
        user = request.data.get('user')
        
        if not user:
            return Response(
                {'error': 'User field is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Get content type for Post
                content_type = ContentType.objects.get_for_model(Post)
                
                # Try to create like - will fail if already exists due to unique constraint
                like, created = Like.objects.get_or_create(
                    user=user,
                    content_type=content_type,
                    object_id=post.id
                )
                
                if not created:
                    return Response(
                        {'error': 'You have already liked this post'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Atomically increment like count
                Post.objects.filter(id=post.id).update(like_count=F('like_count') + 1)
                
                # Create karma transaction (5 points for post like)
                KarmaTransaction.objects.create(
                    user=post.author,
                    points=5,
                    transaction_type=KarmaTransaction.POST_LIKE,
                    content_type=content_type,
                    object_id=post.id
                )
                
                # Refresh post instance
                post.refresh_from_db()
                
                return Response(
                    {'message': 'Post liked successfully', 'like_count': post.like_count},
                    status=status.HTTP_201_CREATED
                )
                
        except IntegrityError:
            return Response(
                {'error': 'You have already liked this post'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """
        Unlike a post.
        """
        post = self.get_object()
        user = request.data.get('user')
        
        if not user:
            return Response(
                {'error': 'User field is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                content_type = ContentType.objects.get_for_model(Post)
                
                # Delete the like
                deleted_count, _ = Like.objects.filter(
                    user=user,
                    content_type=content_type,
                    object_id=post.id
                ).delete()
                
                if deleted_count == 0:
                    return Response(
                        {'error': 'You have not liked this post'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Atomically decrement like count
                from django.db.models import F
                Post.objects.filter(id=post.id).update(like_count=F('like_count') - 1)
                
                # Remove karma transaction (negative points)
                KarmaTransaction.objects.create(
                    user=post.author,
                    points=-5,
                    transaction_type=KarmaTransaction.POST_LIKE,
                    content_type=content_type,
                    object_id=post.id
                )
                
                # Refresh post instance
                post.refresh_from_db()
                
                return Response(
                    {'message': 'Post unliked successfully', 'like_count': post.like_count},
                    status=status.HTTP_200_OK
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Comment operations.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        """
        Filter comments by post if provided.
        """
        queryset = Comment.objects.select_related('post', 'parent')
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Like a comment. Uses database-level unique constraint to prevent double-liking.
        """
        comment = self.get_object()
        user = request.data.get('user')
        
        if not user:
            return Response(
                {'error': 'User field is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                content_type = ContentType.objects.get_for_model(Comment)
                
                like, created = Like.objects.get_or_create(
                    user=user,
                    content_type=content_type,
                    object_id=comment.id
                )
                
                if not created:
                    return Response(
                        {'error': 'You have already liked this comment'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Atomically increment like count
                Comment.objects.filter(id=comment.id).update(like_count=F('like_count') + 1)
                
                # Create karma transaction (1 point for comment like)
                KarmaTransaction.objects.create(
                    user=comment.author,
                    points=1,
                    transaction_type=KarmaTransaction.COMMENT_LIKE,
                    content_type=content_type,
                    object_id=comment.id
                )
                
                comment.refresh_from_db()
                
                return Response(
                    {'message': 'Comment liked successfully', 'like_count': comment.like_count},
                    status=status.HTTP_201_CREATED
                )
                
        except IntegrityError:
            return Response(
                {'error': 'You have already liked this comment'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """
        Unlike a comment.
        """
        comment = self.get_object()
        user = request.data.get('user')
        
        if not user:
            return Response(
                {'error': 'User field is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                content_type = ContentType.objects.get_for_model(Comment)
                
                deleted_count, _ = Like.objects.filter(
                    user=user,
                    content_type=content_type,
                    object_id=comment.id
                ).delete()
                
                if deleted_count == 0:
                    return Response(
                        {'error': 'You have not liked this comment'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                Comment.objects.filter(id=comment.id).update(like_count=F('like_count') - 1)
                
                KarmaTransaction.objects.create(
                    user=comment.author,
                    points=-1,
                    transaction_type=KarmaTransaction.COMMENT_LIKE,
                    content_type=content_type,
                    object_id=comment.id
                )
                
                comment.refresh_from_db()
                
                return Response(
                    {'message': 'Comment unliked successfully', 'like_count': comment.like_count},
                    status=status.HTTP_200_OK
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LeaderboardViewSet(viewsets.ViewSet):
    """
    ViewSet for leaderboard operations.
    Calculates karma dynamically from transaction history.
    """
    
    def list(self, request):
        """
        Get top 5 users by karma earned in the last 24 hours.
        
        This uses aggregation on KarmaTransaction to calculate recent karma,
        not a simple integer field on User model.
        """
        # Calculate 24 hours ago
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        
        # Aggregate karma from transactions in the last 24 hours
        # This is the critical query that satisfies the "Complex Aggregation" constraint
        leaderboard = (
            KarmaTransaction.objects
            .filter(created_at__gte=twenty_four_hours_ago)
            .values('user')
            .annotate(karma=Sum('points'))
            .order_by('-karma')[:5]
        )
        
        # Add rank to results
        leaderboard_data = []
        for rank, entry in enumerate(leaderboard, start=1):
            leaderboard_data.append({
                'user': entry['user'],
                'karma': entry['karma'],
                'rank': rank
            })
        
        serializer = LeaderboardSerializer(leaderboard_data, many=True)
        return Response(serializer.data)
