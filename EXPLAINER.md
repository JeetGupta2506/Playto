# Technical Overview

## 1. N+1 Query Problem: Comment Trees

**Challenge:** Loading 50 nested comments = 51 queries (N+1 nightmare)

**Solution:** Materialized Path Pattern
```python
class Comment(models.Model):
    parent = ForeignKey('self', null=True)
    path = CharField(max_length=500)  # e.g., "1/5/12"
    depth = IntegerField(default=0)
```

**Result:** 1 query loads all comments, tree built in memory
```python
# Single query with path ordering
comments = Comment.objects.filter(post=post).order_by('path')

# Build tree in Python (no DB hits)
for comment in all_comments:
    if comment.parent_id in comment_map:
        parent._prefetched_replies.append(comment)
```
✅ **50 comments = 1 query** (tested)

---

## 2. Dynamic 24-Hour Leaderboard

**Constraint:** No stored karma field, calculate from transaction history

**Implementation:**
```python
twenty_four_hours_ago = timezone.now() - timedelta(hours=24)

leaderboard = (
    KarmaTransaction.objects
    .filter(created_at__gte=twenty_four_hours_ago)
    .values('user')
    .annotate(karma=Sum('points'))
    .order_by('-karma')[:5]
)
```

✅ **Rolling 24h window, handles negative points (unlikes)**

---

## 3. Race Condition Prevention

**Problem:** Double-likes inflate karma

**Solution:** Multi-layer protection
```python
with transaction.atomic():
    like, created = Like.objects.get_or_create(...)  # Atomic
    Post.objects.filter(id=id).update(
        like_count=F('like_count') + 1  # Atomic increment
    )

class Like:
    class Meta:
        unique_together = ('user', 'content_type', 'object_id')  # DB constraint
```

✅ **Database enforces uniqueness, F() expressions prevent race conditions**

---

## 4. Testing: Leaderboard Calculation

**Test Goal:** Verify 24-hour window excludes old transactions

```python
def test_leaderboard_calculation_recent(self):
    now = timezone.now()
    
    # Alice: 2 likes within last 24h (10 karma)
    KarmaTransaction.objects.create(
        user='alice', points=5,
        created_at=now - timedelta(hours=1)
    )
    KarmaTransaction.objects.create(
        user='alice', points=5,
        created_at=now - timedelta(hours=2)
    )
    
    # Charlie: karma from 25h ago (should be EXCLUDED)
    KarmaTransaction.objects.create(
        user='charlie', points=5,
        created_at=now - timedelta(hours=25)
    )
    
    # Query leaderboard
    twenty_four_hours_ago = now - timedelta(hours=24)
    leaderboard = (
        KarmaTransaction.objects
        .filter(created_at__gte=twenty_four_hours_ago)
        .values('user')
        .annotate(karma=Sum('points'))
        .order_by('-karma')
    )
    
    # Assertions
    leaderboard_list = list(leaderboard)
    assert len(leaderboard_list) == 1  # Only Alice
    assert leaderboard_list[0]['user'] == 'alice'
    assert leaderboard_list[0]['karma'] == 10
```

**Why This Test Matters:**
- Validates time-based filtering (critical constraint)
- Confirms dynamic calculation from transactions
- Proves old karma doesn't inflate current scores

✅ **Test passes - Charlie excluded, Alice counted correctly**

---

## Key Learnings

AI generated fast code but missed critical details:
- Race conditions in concurrent requests
- N+1 queries in recursive serialization  
- Time filters in aggregations

**Human intervention required for:** transactions, query optimization, edge cases.
