# FIST Deployment Guide

This guide covers deploying the FIST Content Moderation System to Vercel with PostgreSQL.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **PostgreSQL Database**: Choose one of the following:
   - Vercel Postgres (recommended for Vercel deployments)
   - Supabase (free tier available)
   - Railway
   - AWS RDS
   - Google Cloud SQL

## Step 1: Prepare Your Database

### Option A: Vercel Postgres (Recommended)

1. Go to your Vercel dashboard
2. Create a new project or select existing one
3. Go to the "Storage" tab
4. Click "Create Database" → "Postgres"
5. Follow the setup wizard
6. Copy the connection string from the dashboard

### Option B: Supabase

1. Go to [supabase.com](https://supabase.com) and create an account
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string (URI format)

### Option C: Railway

1. Go to [railway.app](https://railway.app) and create an account
2. Create a new project
3. Add a PostgreSQL service
4. Copy the connection string from the service details

## Step 2: Deploy to Vercel

### Method 1: Vercel CLI (Recommended)

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from your project directory**:
   ```bash
   vercel --prod
   ```

4. **Follow the prompts**:
   - Link to existing project or create new one
   - Set build settings (should auto-detect)

### Method 2: GitHub Integration

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Add PostgreSQL support and Vercel deployment"
   git push origin main
   ```

2. **Connect to Vercel**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Configure build settings (should auto-detect)

## Step 3: Configure Environment Variables

In your Vercel dashboard, go to your project → Settings → Environment Variables and add:

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://username:password@hostname:port/database_name

# AI Configuration
AI_API_KEY=your-deepseek-api-key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-chat

# Authentication
SECRET_KEY=your-very-secure-secret-key-change-this
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

# User Management
MAX_USERS=100
REQUIRE_INVITATION_CODE=true
USER_TOKEN_EXPIRE_MINUTES=60
```

### Optional Variables

```bash
# API Configuration (usually not needed for Vercel)
DEBUG=false

# Content Moderation (uses defaults if not set)
DEFAULT_PERCENTAGES=[0.8,0.6,0.4,0.2]
DEFAULT_THRESHOLDS=[500,1000,3000]
```

## Step 4: Verify Deployment

1. **Check deployment status** in Vercel dashboard
2. **Access API documentation**:
   ```
   https://your-app.vercel.app/docs
   ```

## Step 5: Initialize Admin User

After successful deployment, you'll need to create the initial admin user. You can do this by:

1. **Using the API directly** (if admin credentials are set in environment):
   ```bash
   curl -X POST https://your-app.vercel.app/api/admin/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "your-admin-password"}'
   ```

2. **Database initialization** happens automatically on first startup

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify `DATABASE_URL` is correct
   - Check database server is accessible
   - Ensure database exists

2. **Environment Variables Not Loading**:
   - Check variable names are exact (case-sensitive)
   - Redeploy after adding variables
   - Check Vercel dashboard for variable values

3. **Build Failures**:
   - Check `requirements.txt` is present
   - Verify Python version compatibility
   - Check build logs in Vercel dashboard

4. **API Endpoints Not Working**:
   - Verify `api/index.py` is present
   - Check `vercel.json` configuration
   - Review function logs in Vercel dashboard

### Debugging

1. **Check Vercel Function Logs**:
   - Go to Vercel dashboard → Functions tab
   - Click on function to see logs

2. **Test Locally with PostgreSQL**:
   ```bash
   export DATABASE_URL="your-postgresql-url"
   python app.py
   ```

3. **Verify Database Tables**:
   - Connect to your PostgreSQL database
   - Check if tables were created automatically

## Performance Considerations

1. **Database Connection Pooling**: PostgreSQL handles this automatically
2. **Function Timeout**: Vercel functions have a 30-second timeout (configured in `vercel.json`)
3. **Cold Starts**: First request after inactivity may be slower

## Security Best Practices

1. **Use Strong Passwords**: For admin and database credentials
2. **Rotate Secrets**: Regularly update `SECRET_KEY` and API keys
3. **Database Security**: Use SSL connections (enabled by default with most providers)
4. **Environment Variables**: Never commit secrets to version control

## Monitoring

1. **Vercel Analytics**: Monitor function performance and errors
2. **Database Monitoring**: Use your database provider's monitoring tools
3. **API Usage**: Monitor through your application's usage tracking

## Scaling

1. **Database**: Most PostgreSQL providers offer automatic scaling
2. **Vercel Functions**: Automatically scale based on demand
3. **Rate Limiting**: Consider implementing rate limiting for production use

## Backup and Recovery

1. **Database Backups**: Configure automatic backups with your database provider
2. **Code Backups**: Use Git for version control
3. **Environment Variables**: Keep a secure backup of your environment configuration

## Support

For deployment issues:
1. Check Vercel documentation
2. Review database provider documentation
3. Check application logs for specific error messages
