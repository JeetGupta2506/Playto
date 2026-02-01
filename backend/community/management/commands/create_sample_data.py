from django.core.management.base import BaseCommand
from community.models import Post, Comment, KarmaTransaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Populates the database with sample data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')

        # Create sample posts
        posts_data = [
            {
                'author': 'alice',
                'content': 'Welcome to Playto! This is our first community post. What do you think about the new platform?'
            },
            {
                'author': 'bob',
                'content': 'Just finished building a new feature. The threaded comments work amazingly well! Check out how nested replies render.'
            },
            {
                'author': 'charlie',
                'content': 'Has anyone tried the leaderboard yet? I\'m curious how the karma system works. Post likes give 5 points, comment likes give 1 point.'
            },
            {
                'author': 'diana',
                'content': 'The UI is beautiful! Love the gradient avatars and smooth animations. Great work on the design.'
            },
            {
                'author': 'eve',
                'content': 'Quick question: How are the comments loaded so efficiently? I noticed no lag even with nested threads.'
            },
        ]

        posts = []
        for data in posts_data:
            post = Post.objects.create(**data)
            posts.append(post)
            self.stdout.write(f'Created post by {data["author"]}')

        # Create sample comments
        # Post 1 comments
        comment1 = Comment.objects.create(
            post=posts[0],
            author='bob',
            content='Great to be here! The platform looks very promising.'
        )
        
        Comment.objects.create(
            post=posts[0],
            parent=comment1,
            author='alice',
            content='Thanks Bob! Let me know if you have any suggestions.'
        )
        
        comment2 = Comment.objects.create(
            post=posts[0],
            author='charlie',
            content='I agree, this is exactly what we needed for community discussions.'
        )
        
        Comment.objects.create(
            post=posts[0],
            parent=comment2,
            author='diana',
            content='Absolutely! The threaded comments make conversations so much easier to follow.'
        )

        # Post 2 comments
        comment3 = Comment.objects.create(
            post=posts[1],
            author='alice',
            content='The nested replies look perfect! How deep does the nesting go?'
        )
        
        Comment.objects.create(
            post=posts[1],
            parent=comment3,
            author='bob',
            content='It can go pretty deep! The materialized path pattern handles it efficiently.'
        )

        # Post 3 comments
        Comment.objects.create(
            post=posts[2],
            author='diana',
            content='The leaderboard updates in real-time based on the last 24 hours of activity!'
        )

        # Post 4 comments
        Comment.objects.create(
            post=posts[3],
            author='eve',
            content='The color scheme is really nice. Modern but not too flashy.'
        )

        # Post 5 comments
        comment4 = Comment.objects.create(
            post=posts[4],
            author='charlie',
            content='It\'s using a clever optimization technique. All comments are loaded in a single query!'
        )
        
        Comment.objects.create(
            post=posts[4],
            parent=comment4,
            author='eve',
            content='That\'s impressive! No N+1 queries at all?'
        )
        
        Comment.objects.create(
            post=posts[4],
            parent=comment4,
            author='charlie',
            content='Correct! The path-based ordering makes it super efficient.'
        )

        self.stdout.write(f'Created {Comment.objects.count()} comments')

        # Create karma transactions (simulate recent activity)
        now = timezone.now()
        
        karma_data = [
            # Alice - lots of recent activity
            ('alice', 5, KarmaTransaction.POST_LIKE, now - timedelta(hours=1)),
            ('alice', 5, KarmaTransaction.POST_LIKE, now - timedelta(hours=3)),
            ('alice', 1, KarmaTransaction.COMMENT_LIKE, now - timedelta(hours=5)),
            ('alice', 1, KarmaTransaction.COMMENT_LIKE, now - timedelta(hours=7)),
            
            # Bob - moderate activity
            ('bob', 5, KarmaTransaction.POST_LIKE, now - timedelta(hours=2)),
            ('bob', 1, KarmaTransaction.COMMENT_LIKE, now - timedelta(hours=4)),
            ('bob', 1, KarmaTransaction.COMMENT_LIKE, now - timedelta(hours=6)),
            
            # Charlie - some activity
            ('charlie', 5, KarmaTransaction.POST_LIKE, now - timedelta(hours=8)),
            ('charlie', 1, KarmaTransaction.COMMENT_LIKE, now - timedelta(hours=10)),
            
            # Diana - recent activity
            ('diana', 1, KarmaTransaction.COMMENT_LIKE, now - timedelta(hours=12)),
            
            # Eve - older activity (won't show in 24h leaderboard)
            ('eve', 5, KarmaTransaction.POST_LIKE, now - timedelta(hours=30)),
        ]

        for user, points, trans_type, created_at in karma_data:
            KarmaTransaction.objects.create(
                user=user,
                points=points,
                transaction_type=trans_type,
                created_at=created_at
            )

        self.stdout.write(f'Created {KarmaTransaction.objects.count()} karma transactions')

        # Update like counts on posts and comments based on karma transactions
        for post in posts:
            # Simulate some likes
            likes_count = KarmaTransaction.objects.filter(
                transaction_type=KarmaTransaction.POST_LIKE,
                points__gt=0
            ).count() // len(posts)
            post.like_count = likes_count
            post.save()

        self.stdout.write(self.style.SUCCESS('Successfully created sample data!'))
        self.stdout.write(self.style.SUCCESS('\nYou can now:'))
        self.stdout.write('  - View posts at http://localhost:3000')
        self.stdout.write('  - Check the leaderboard (Alice should be #1)')
        self.stdout.write('  - Test adding comments and likes')
