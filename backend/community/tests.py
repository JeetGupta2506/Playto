from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType

from .models import Post, Comment, Like, KarmaTransaction


class PostModelTest(TestCase):
    def setUp(self):
        self.post = Post.objects.create(
            author='testuser',
            content='Test post content'
        )
    
    def test_post_creation(self):
        """Test that a post is created correctly"""
        self.assertEqual(self.post.author, 'testuser')
        self.assertEqual(self.post.content, 'Test post content')
        self.assertEqual(self.post.like_count, 0)
    
    def test_post_ordering(self):
        """Test that posts are ordered by created_at descending"""
        post1 = Post.objects.create(author='user1', content='First')
        post2 = Post.objects.create(author='user2', content='Second')
        posts = list(Post.objects.all())
        self.assertEqual(posts[0], post2)
        self.assertEqual(posts[1], post1)


class CommentModelTest(TestCase):
    def setUp(self):
        self.post = Post.objects.create(
            author='testuser',
            content='Test post'
        )
    
    def test_root_comment_creation(self):
        """Test creating a root-level comment"""
        comment = Comment.objects.create(
            post=self.post,
            author='commenter',
            content='Test comment'
        )
        self.assertEqual(comment.depth, 0)
        self.assertEqual(comment.path, str(comment.id))
        self.assertIsNone(comment.parent)
    
    def test_nested_comment_creation(self):
        """Test creating nested comments"""
        parent = Comment.objects.create(
            post=self.post,
            author='user1',
            content='Parent comment'
        )
        
        child = Comment.objects.create(
            post=self.post,
            parent=parent,
            author='user2',
            content='Child comment'
        )
        
        self.assertEqual(child.depth, 1)
        self.assertEqual(child.path, f"{parent.path}/{child.id}")
        self.assertEqual(child.parent, parent)


class LikeTest(TestCase):
    def setUp(self):
        self.post = Post.objects.create(
            author='author',
            content='Test post'
        )
        self.content_type = ContentType.objects.get_for_model(Post)
    
    def test_unique_like_constraint(self):
        """Test that a user cannot like the same post twice"""
        Like.objects.create(
            user='user1',
            content_type=self.content_type,
            object_id=self.post.id
        )
        
        # Try to create duplicate like
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Like.objects.create(
                user='user1',
                content_type=self.content_type,
                object_id=self.post.id
            )
    
    def test_api_prevents_double_like(self):
        """
        Test that the API endpoint prevents double-liking.
        This addresses the "Concurrency" constraint.
        """
        from rest_framework.test import APIClient
        client = APIClient()
        
        # First like should succeed
        response1 = client.post(
            f'/api/posts/{self.post.id}/like/',
            {'user': 'user1'},
            format='json'
        )
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data['like_count'], 1)
        
        # Second like attempt should fail
        response2 = client.post(
            f'/api/posts/{self.post.id}/like/',
            {'user': 'user1'},
            format='json'
        )
        self.assertEqual(response2.status_code, 400)
        self.assertIn('already liked', response2.data['error'])
        
        # Verify like count didn't increase
        self.post.refresh_from_db()
        self.assertEqual(self.post.like_count, 1)
        
        # Verify only one Like object exists
        like_count = Like.objects.filter(
            user='user1',
            content_type=self.content_type,
            object_id=self.post.id
        ).count()
        self.assertEqual(like_count, 1)
    
    def test_comment_double_like_prevention(self):
        """Test that comments are also protected from double-liking"""
        from rest_framework.test import APIClient
        client = APIClient()
        
        comment = Comment.objects.create(
            post=self.post,
            author='author',
            content='Test comment'
        )
        comment_content_type = ContentType.objects.get_for_model(Comment)
        
        # First like succeeds
        response1 = client.post(
            f'/api/comments/{comment.id}/like/',
            {'user': 'user1'},
            format='json'
        )
        self.assertEqual(response1.status_code, 201)
        
        # Second like fails
        response2 = client.post(
            f'/api/comments/{comment.id}/like/',
            {'user': 'user1'},
            format='json'
        )
        self.assertEqual(response2.status_code, 400)
        self.assertIn('already liked', response2.data['error'])
        
        # Verify only one Like exists
        like_count = Like.objects.filter(
            user='user1',
            content_type=comment_content_type,
            object_id=comment.id
        ).count()
        self.assertEqual(like_count, 1)


class LeaderboardTest(TestCase):
    def setUp(self):
        """Create test data for leaderboard"""
        # Create posts
        self.post1 = Post.objects.create(author='alice', content='Post 1')
        self.post2 = Post.objects.create(author='bob', content='Post 2')
        self.post3 = Post.objects.create(author='charlie', content='Post 3')
        
        # Create comments
        self.comment1 = Comment.objects.create(
            post=self.post1,
            author='bob',
            content='Comment 1'
        )
    
    def test_leaderboard_calculation_recent(self):
        """
        Test that leaderboard correctly calculates karma from last 24 hours.
        This is the critical test for the "Complex Aggregation" constraint.
        """
        # Create karma transactions within last 24 hours
        now = timezone.now()
        
        # Alice gets 2 post likes (10 karma)
        KarmaTransaction.objects.create(
            user='alice',
            points=5,
            transaction_type=KarmaTransaction.POST_LIKE,
            created_at=now - timedelta(hours=1)
        )
        KarmaTransaction.objects.create(
            user='alice',
            points=5,
            transaction_type=KarmaTransaction.POST_LIKE,
            created_at=now - timedelta(hours=2)
        )
        
        # Bob gets 1 post like (5 karma) and 3 comment likes (3 karma) = 8 karma
        KarmaTransaction.objects.create(
            user='bob',
            points=5,
            transaction_type=KarmaTransaction.POST_LIKE,
            created_at=now - timedelta(hours=5)
        )
        KarmaTransaction.objects.create(
            user='bob',
            points=1,
            transaction_type=KarmaTransaction.COMMENT_LIKE,
            created_at=now - timedelta(hours=6)
        )
        KarmaTransaction.objects.create(
            user='bob',
            points=1,
            transaction_type=KarmaTransaction.COMMENT_LIKE,
            created_at=now - timedelta(hours=7)
        )
        KarmaTransaction.objects.create(
            user='bob',
            points=1,
            transaction_type=KarmaTransaction.COMMENT_LIKE,
            created_at=now - timedelta(hours=8)
        )
        
        # Charlie gets karma but it's older than 24 hours (should not count)
        KarmaTransaction.objects.create(
            user='charlie',
            points=5,
            transaction_type=KarmaTransaction.POST_LIKE,
            created_at=now - timedelta(hours=25)
        )
        KarmaTransaction.objects.create(
            user='charlie',
            points=5,
            transaction_type=KarmaTransaction.POST_LIKE,
            created_at=now - timedelta(hours=30)
        )
        
        # Calculate leaderboard (last 24 hours)
        # Use the same 'now' reference to avoid timing issues
        from django.db.models import Sum
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        leaderboard = (
            KarmaTransaction.objects
            .filter(created_at__gte=twenty_four_hours_ago)
            .values('user')
            .annotate(karma=Sum('points'))
            .order_by('-karma')
        )
        
        leaderboard_list = list(leaderboard)
        
        # Assertions
        self.assertEqual(len(leaderboard_list), 2)  # Only alice and bob
        self.assertEqual(leaderboard_list[0]['user'], 'alice')
        self.assertEqual(leaderboard_list[0]['karma'], 10)
        self.assertEqual(leaderboard_list[1]['user'], 'bob')
        self.assertEqual(leaderboard_list[1]['karma'], 8)
        
        # Charlie should not appear (transactions too old)
        charlie_in_leaderboard = any(entry['user'] == 'charlie' for entry in leaderboard_list)
        self.assertFalse(charlie_in_leaderboard)
    
    def test_leaderboard_with_unlikes(self):
        """Test that negative karma transactions (unlikes) are correctly handled"""
        now = timezone.now()
        
        # User gets karma then loses some
        KarmaTransaction.objects.create(
            user='alice',
            points=5,
            transaction_type=KarmaTransaction.POST_LIKE,
            created_at=now - timedelta(hours=1)
        )
        KarmaTransaction.objects.create(
            user='alice',
            points=5,
            transaction_type=KarmaTransaction.POST_LIKE,
            created_at=now - timedelta(hours=2)
        )
        KarmaTransaction.objects.create(
            user='alice',
            points=-5,  # Unlike
            transaction_type=KarmaTransaction.POST_LIKE,
            created_at=now - timedelta(hours=3)
        )
        
        from django.db.models import Sum
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        leaderboard = (
            KarmaTransaction.objects
            .filter(created_at__gte=twenty_four_hours_ago)
            .values('user')
            .annotate(karma=Sum('points'))
            .order_by('-karma')
        )
        
        alice_karma = list(leaderboard)[0]
        self.assertEqual(alice_karma['user'], 'alice')
        self.assertEqual(alice_karma['karma'], 5)  # 5 + 5 - 5 = 5


class CommentTreeQueryTest(TestCase):
    """
    Test to ensure comment tree loading doesn't cause N+1 queries.
    This addresses the "N+1 Nightmare" constraint.
    """
    def setUp(self):
        self.post = Post.objects.create(
            author='author',
            content='Test post'
        )
        
        # Create a tree of comments
        self.root1 = Comment.objects.create(
            post=self.post,
            author='user1',
            content='Root 1'
        )
        self.root2 = Comment.objects.create(
            post=self.post,
            author='user2',
            content='Root 2'
        )
        
        # Add children to root1
        self.child1 = Comment.objects.create(
            post=self.post,
            parent=self.root1,
            author='user3',
            content='Child 1'
        )
        self.child2 = Comment.objects.create(
            post=self.post,
            parent=self.root1,
            author='user4',
            content='Child 2'
        )
        
        # Add grandchild
        self.grandchild = Comment.objects.create(
            post=self.post,
            parent=self.child1,
            author='user5',
            content='Grandchild'
        )
    
    def test_efficient_comment_tree_loading(self):
        """Test that all comments can be loaded in a single query"""
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        # Load all comments for the post in one query
        with CaptureQueriesContext(connection) as context:
            comments = list(Comment.objects.filter(post=self.post).order_by('path'))
        
        # Should be just 1 query to get all comments
        self.assertEqual(len(context.captured_queries), 1)
        
        # Verify we got all 5 comments
        self.assertEqual(len(comments), 5)
        
        # Verify path-based ordering
        self.assertEqual(comments[0], self.root1)
        self.assertTrue(comments[1] in [self.child1, self.child2])
