# Deployment Guide for Jorp

This guide will help you deploy your Django Korean vocabulary learning application to various platforms.

## Prerequisites

- Your code is already pushed to GitHub at: `https://github.com/Vyacheslav2323/lexipark.git`
- You have a GitHub account

## Deployment Options

### Option 1: Render (Recommended - Free Tier Available)

1. **Sign up for Render**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account

2. **Create a new Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `Vyacheslav2323/lexipark`

3. **Configure the service**
   - **Name**: `jorp-korean-vocab`
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn jorp.wsgi:application`

4. **Add Environment Variables**
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

5. **Add PostgreSQL Database**
   - Go to "New +" → "PostgreSQL"
   - Create a new database
   - Copy the DATABASE_URL to your web service environment variables

### Option 2: Railway

1. **Sign up for Railway**
   - Go to [railway.app](https://railway.app)
   - Sign up with your GitHub account

2. **Deploy from GitHub**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Add Environment Variables**
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ```

4. **Add PostgreSQL**
   - Go to "New" → "Database" → "PostgreSQL"
   - Railway will automatically set the DATABASE_URL

### Option 3: Heroku

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Or download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

4. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

5. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key-here
   heroku config:set DEBUG=False
   ```

6. **Deploy**
   ```bash
   git push heroku main
   ```

7. **Run migrations**
   ```bash
   heroku run python manage.py migrate
   ```

## Environment Variables

Set these environment variables in your deployment platform:

### Required Variables
```
SECRET_KEY=your-secret-key-here
DEBUG=False
```

### Database Variables (if not using DATABASE_URL)
```
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=5432
```

### Optional Variables
```
PAPAGO_CLIENT_ID=your-papago-client-id
PAPAGO_CLIENT_SECRET=your-papago-client-secret
```

## Generating a Secret Key

Generate a secure secret key:
```python
import secrets
print(secrets.token_urlsafe(50))
```

## Post-Deployment Steps

1. **Run migrations**
   ```bash
   python manage.py migrate
   ```

2. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

3. **Collect static files**
   ```bash
   python manage.py collectstatic --no-input
   ```

## Troubleshooting

### Common Issues

1. **Build fails with MeCab error**
   - MeCab is not available on most deployment platforms
   - The application will work without MeCab, but Korean text analysis will be limited
   - Consider using a different Korean NLP service for production

2. **Database connection issues**
   - Ensure your DATABASE_URL is correct
   - Check that your database is accessible from your deployment platform

3. **Static files not loading**
   - Ensure STATIC_ROOT is set correctly
   - Run `python manage.py collectstatic` during build

4. **Environment variables not set**
   - Double-check all required environment variables are set
   - Restart your application after setting environment variables

### Getting Help

- Check the deployment platform's logs for error messages
- Ensure all required packages are in `requirements.txt`
- Verify your `build.sh` script is executable

## Custom Domain (Optional)

After deployment, you can add a custom domain:

1. **Render**: Go to your service → Settings → Custom Domains
2. **Railway**: Go to your project → Settings → Domains
3. **Heroku**: `heroku domains:add yourdomain.com`

## Monitoring

- **Render**: Built-in monitoring and logs
- **Railway**: Built-in monitoring and logs  
- **Heroku**: `heroku logs --tail` for real-time logs

## Security Notes

- Never commit `.env` files to Git
- Use strong, unique secret keys
- Set `DEBUG=False` in production
- Enable HTTPS (most platforms do this automatically)
- Regularly update dependencies 