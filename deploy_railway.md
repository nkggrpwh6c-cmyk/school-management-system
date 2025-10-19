# Deploy School Management System to Railway

## Prerequisites
1. Railway account (free at railway.app)
2. Git installed
3. Railway CLI (optional)

## Step-by-Step Deployment

### 1. Connect GitHub Repository
1. Push your code to GitHub
2. Go to railway.app
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository

### 2. Configure Environment Variables
In Railway dashboard, add these variables:

```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app
DJANGO_SETTINGS_MODULE=config.settings_production
```

### 3. Add PostgreSQL Database
1. In Railway dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically set DATABASE_URL

### 4. Deploy
Railway will automatically deploy when you push to GitHub.

### 5. Run Migrations
In Railway dashboard, go to your app and run:
```bash
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

## Advantages of Railway
- ✅ Free tier available
- ✅ Automatic deployments
- ✅ Built-in PostgreSQL
- ✅ Easy scaling
- ✅ Custom domains
- ✅ SSL certificates

## Custom Domain Setup
1. Buy domain from any registrar
2. In Railway dashboard, go to Settings → Domains
3. Add your domain
4. Configure DNS records as shown
5. Update ALLOWED_HOSTS

## Environment Variables
```
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourschool.com
```

## Monitoring
- View logs in Railway dashboard
- Monitor resource usage
- Set up alerts for downtime

## Backup
Railway provides automatic backups for PostgreSQL databases.
