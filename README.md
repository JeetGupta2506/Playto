# Playto Community Feed

A full-stack community discussion platform with threaded comments, gamification, and dynamic leaderboards.

## Features

- **Community Feed:** Text posts with author attribution and like counts
- **Threaded Comments:** Reddit-style nested comment threads
- **Gamification System:** Karma points (5 for post likes, 1 for comment likes)
- **Dynamic Leaderboard:** Top 5 users by karma earned in the last 24 hours
- **Race Condition Protection:** Database-level constraints prevent double-liking
- **Optimized Queries:** No N+1 queries when loading comment trees

## Tech Stack

### Backend
- Django 4.2 + Django REST Framework
- SQLite (development) / PostgreSQL (production-ready)
- Python 3.11

### Frontend
- React 18
- Tailwind CSS
- Axios for API calls

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd Playto

# Start with Docker Compose
docker-compose up --build

# The app will be available at:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create a superuser (optional, for admin access)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The backend API will be available at `http://localhost:8000/api`

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Posts
- `GET /api/posts/` - List all posts
- `POST /api/posts/` - Create a new post
- `GET /api/posts/{id}/` - Get a post with its comment tree
- `POST /api/posts/{id}/like/` - Like a post
- `POST /api/posts/{id}/unlike/` - Unlike a post

### Comments
- `GET /api/comments/` - List all comments (filter by `?post=<id>`)
- `POST /api/comments/` - Create a new comment
- `POST /api/comments/{id}/like/` - Like a comment
- `POST /api/comments/{id}/unlike/` - Unlike a comment

### Leaderboard
- `GET /api/leaderboard/` - Get top 5 users by karma (last 24h)

## Testing

```bash
cd backend
python manage.py test community
```

Tests cover:
- Model creation and relationships
- Unique constraint enforcement (prevent double-liking)
- Leaderboard calculation from transaction history
- N+1 query prevention for comment trees

## Project Structure

```
Playto/
├── backend/
│   ├── config/              # Django settings
│   ├── community/           # Main app
│   │   ├── models.py       # Post, Comment, Like, KarmaTransaction models
│   │   ├── views.py        # DRF ViewSets
│   │   ├── serializers.py  # DRF Serializers
│   │   ├── tests.py        # Test suite
│   │   └── admin.py        # Admin configuration
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── Post.jsx
│   │   │   ├── Comment.jsx
│   │   │   └── Leaderboard.jsx
│   │   ├── services/       # API integration
│   │   │   └── api.js
│   │   ├── App.js          # Main app component
│   │   └── index.js        # Entry point
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── README.md
└── EXPLAINER.md
```

## Environment Variables

### Backend (.env)
```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000/api
```

## Key Technical Decisions

### 1. Nested Comments (Materialized Path)
- Comments use a hybrid approach: adjacency list + materialized path
- The `path` field (e.g., "1/2/3") enables efficient tree traversal
- All comments for a post can be loaded in **1 query** and sorted by path
- See `EXPLAINER.md` for detailed explanation

### 2. Karma Calculation
- Karma is **not** stored as a simple integer on the User model
- Instead, `KarmaTransaction` records every karma change with timestamp
- Leaderboard is calculated dynamically: `SUM(points) WHERE created_at >= 24h ago`
- This enables accurate time-based leaderboards without cron jobs

### 3. Race Condition Prevention
- Database-level unique constraint on `Like` model: `(user, content_type, object_id)`
- Atomic transactions with `F()` expressions for like count updates
- Even with concurrent requests, users cannot double-like

## Deployment

The app is ready for deployment on:
- **Railway** (recommended for Django)
- **Vercel** (frontend)
- **Heroku**
- **AWS / DigitalOcean**

For production:
1. Set `DEBUG=False`
2. Configure PostgreSQL database
3. Set strong `SECRET_KEY`
4. Configure static file serving (WhiteNoise included)
5. Set proper `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`

## Admin Panel

Access the Django admin at `http://localhost:8000/admin/` to:
- View and manage posts, comments, likes
- Inspect karma transactions
- Monitor user activity

## License

MIT
