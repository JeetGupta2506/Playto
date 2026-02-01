# Free Tier Deployment Guide

## 🎯 Best Free Option: Render

Both backend and frontend free, easiest setup, no credit card required.

---

## Step-by-Step: Deploy on Render (100% Free)

### Part 1: Deploy Backend (Django API)

1. **Push code to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Go to [render.com](https://render.com)** → Sign up with GitHub

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Select repository

4. **Configure Backend Service:**
   ```
   Name: playto-backend
   Region: Pick closest to you
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
   ```

5. **Add Environment Variables:**
   ```
   SECRET_KEY = django-insecure-generate-your-own-secret-key-here-12345
   DEBUG = False
   ALLOWED_HOSTS = .onrender.com
   CORS_ALLOWED_ORIGINS = https://your-app-name.vercel.app
   DATABASE_URL = (leave empty, Render provides SQLite)
   ```

6. **Click "Create Web Service"** → Wait 5-10 minutes for deploy

7. **Run Migrations** (in Render Shell):
   - Go to your service → "Shell" tab
   - Run:
   ```bash
   python manage.py migrate
   python manage.py create_sample_data
   ```

8. **Copy your backend URL** → `https://playto-backend.onrender.com`

---

### Part 2: Deploy Frontend (React)

**Option A: Vercel (Recommended)**

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Deploy:**
   ```bash
   cd frontend
   vercel --prod
   ```

3. **During setup:**
   - Link to existing project? → No
   - Project name? → playto-frontend
   - Directory? → `./` (current)
   - Build command? → `npm run build`
   - Output directory? → `build`

4. **Add Environment Variable:**
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add: `REACT_APP_API_URL` = `https://playto-backend.onrender.com/api`
   - Redeploy: `vercel --prod`

**Option B: Render Static Site**

1. **In Render Dashboard**
   - Click "New +" → "Static Site"
   - Connect same repo

2. **Configure:**
   ```
   Name: playto-frontend
   Branch: main
   Root Directory: frontend
   Build Command: npm install && npm run build
   Publish Directory: build
   ```

3. **Add Environment Variable:**
   ```
   REACT_APP_API_URL = https://playto-backend.onrender.com/api
   ```

---

## Alternative: Railway (Free 500 hours/month)

### Backend + Frontend on Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy Backend
cd backend
railway init
railway up

# Deploy Frontend
cd ../frontend
railway init
railway up
```

**Set Environment Variables in Railway Dashboard:**

Backend:
```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=*.railway.app
CORS_ALLOWED_ORIGINS=https://your-frontend.railway.app
```

Frontend:
```
REACT_APP_API_URL=https://your-backend.railway.app/api
```

---

## Update CORS After Deployment

Once you have your frontend URL, update backend environment variables:

```
CORS_ALLOWED_ORIGINS = https://your-actual-frontend-url.vercel.app
```

Then redeploy backend or restart the service.

---

## Testing Your Deployment

1. **Backend Health Check:**
   ```bash
   curl https://your-backend.onrender.com/api/posts/
   ```

2. **Frontend:**
   - Open browser to your frontend URL
   - Try creating a post
   - Check if leaderboard loads
   - Open DevTools → Network tab → verify API calls work

---

## Free Tier Limitations

| Platform | Backend | Frontend | Limitations |
|----------|---------|----------|-------------|
| **Render** | ✅ Free | ✅ Free | Sleeps after 15 min inactivity (wakes in ~30s) |
| **Railway** | ✅ 500hrs | ✅ 500hrs | $5 credit/month, need credit card |
| **Vercel** | ❌ | ✅ Free | Frontend only, 100GB bandwidth |
| **Fly.io** | ✅ Free | ✅ Free | 3 VMs free, 160GB transfer |

**Recommendation:** Render (backend) + Vercel (frontend) = 100% free, no credit card.

---

## Troubleshooting

**Backend won't start:**
- Check logs in Render Dashboard
- Verify `requirements.txt` includes all dependencies
- Ensure `gunicorn` is in requirements.txt

**CORS errors:**
- Update `CORS_ALLOWED_ORIGINS` with exact frontend URL
- Include `https://` and no trailing slash
- Redeploy backend after changes

**Frontend can't reach backend:**
- Check `REACT_APP_API_URL` is correct
- Verify backend is running (check Render logs)
- Test backend URL directly in browser

**Database migrations:**
```bash
# In Render Shell
python manage.py migrate
python manage.py showmigrations
```

---

## Quick Deploy Commands

```bash
# 1. Commit code
git add .
git commit -m "Deploy to production"
git push

# 2. Deploy frontend to Vercel
cd frontend
vercel --prod

# 3. Backend deploys automatically on Render via GitHub

# 4. Run migrations in Render Shell
python manage.py migrate
python manage.py create_sample_data
```

Done! 🚀
