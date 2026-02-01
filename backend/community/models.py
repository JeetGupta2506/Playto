from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from django.utils import timezone


class Post(models.Model):
    """
    Represents a post in the community feed.
    """
    author = models.CharField(max_length=255)
    content = models.TextField()
    like_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"Post by {self.author}: {self.content[:50]}"


class Comment(models.Model):
    """
    Represents a comment on a post or another comment (threaded).
    Uses adjacency list pattern for tree structure.
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    author = models.CharField(max_length=255)
    content = models.TextField()
    like_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Denormalized path for efficient tree queries (materialized path pattern)
    # Format: "1/2/3" represents hierarchy of comment IDs
    path = models.CharField(max_length=500, blank=True, editable=False)
    depth = models.IntegerField(default=0, editable=False)
    
    class Meta:
        ordering = ['path']
        indexes = [
            models.Index(fields=['post', 'path']),
            models.Index(fields=['parent']),
            models.Index(fields=['author']),
            models.Index(fields=['-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Automatically calculate path and depth on save.
        This enables efficient tree traversal without recursive queries.
        """
        if self.parent:
            self.depth = self.parent.depth + 1
            # Create path after getting ID
            if not self.pk:
                super().save(*args, **kwargs)
                self.path = f"{self.parent.path}/{self.pk}"
                kwargs['force_insert'] = False
        else:
            self.depth = 0
            if not self.pk:
                super().save(*args, **kwargs)
                self.path = str(self.pk)
                kwargs['force_insert'] = False
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Comment by {self.author} on Post {self.post_id}"


class Like(models.Model):
    """
    Generic like model that can be applied to Posts or Comments.
    Uses composite unique constraint to prevent double-liking.
    """
    user = models.CharField(max_length=255)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user} liked {self.content_type.model} #{self.object_id}"


class KarmaTransaction(models.Model):
    """
    Stores karma transactions for accurate historical tracking.
    This enables dynamic calculation of 24-hour leaderboards.
    """
    POST_LIKE = 'post_like'
    COMMENT_LIKE = 'comment_like'
    
    TRANSACTION_TYPES = [
        (POST_LIKE, 'Post Like'),
        (COMMENT_LIKE, 'Comment Like'),
    ]
    
    user = models.CharField(max_length=255)
    points = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    # References for tracking (optional, for auditing)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user} earned {self.points} karma ({self.transaction_type})"
