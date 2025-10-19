# Deploy School Management System to Heroku

## Prerequisites
1. Heroku account (free at heroku.com)
2. Git installed
3. Heroku CLI installed

## Step-by-Step Deployment

### 1. Install Heroku CLI
Download from: https://devcenter.heroku.com/articles/heroku-cli

### 2. Login to Heroku
```bash
heroku login
```

### 3. Create Heroku App
```bash
heroku create your-school-management-app
```

### 4. Add PostgreSQL Database
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

### 5. Set Environment Variables
```bash
heroku config:set SECRET_KEY=your-secret-key-here
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=your-school-management-app.herokuapp.com
```

### 6. Deploy
```bash
git add .
git commit -m "Deploy school management system"
git push heroku main
```

### 7. Run Migrations
```bash
heroku run python manage.py migrate
```

### 8. Create Superuser
```bash
heroku run python manage.py createsuperuser
```

### 9. Collect Static Files
```bash
heroku run python manage.py collectstatic --noinput
```

### 10. Open Your App
```bash
heroku open
```

## Environment Variables for Production
Set these in Heroku dashboard or via CLI:

```
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app-name.herokuapp.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourschool.com
```

## Custom Domain (Optional)
1. Buy a domain (e.g., from Namecheap, GoDaddy)
2. Add domain to Heroku app
3. Configure DNS settings
4. Update ALLOWED_HOSTS

## Monitoring
- Use Heroku logs: `heroku logs --tail`
- Monitor performance in Heroku dashboard
- Set up error tracking (Sentry)

## Backup Strategy
```bash
# Backup database
heroku pg:backups:capture
heroku pg:backups:download
```

## Scaling
- Upgrade to paid dynos for better performance
- Add Redis for caching
- Use CDN for static files
