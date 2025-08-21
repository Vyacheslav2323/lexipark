# Free Access Admin Features

This document explains how to use the new admin features for granting free access to users.

## Features Added

### 1. Enhanced Django Admin Interface

The Django admin now includes:
- **Subscription Admin**: Manage user subscriptions with bulk actions
- **User Admin**: View and manage user subscription status
- **PromoCode Admin**: Create and manage promotional codes

### 2. Custom Admin Page

A dedicated page for managing free access at `/billing/admin/free-access-page/`

### 3. API Endpoints

Programmatic access for admins:
- `POST /billing/admin/grant-free-access/`
- `POST /billing/admin/revoke-free-access/`

### 4. Management Command

Command-line tool for bulk operations:
```bash
python manage.py grant_free_access --users user1 user2 --lifetime
python manage.py grant_free_access --file users.txt --trial-days 60
```

## How to Use

### Via Django Admin

1. **Go to Django Admin** (`/admin/`)
2. **Navigate to Subscriptions** or **Users**
3. **Select users** you want to grant access to
4. **Choose action** from the dropdown:
   - "Grant lifetime free access"
   - "Extend trial by 30 days"
   - "Go to Free Access Management Page"

### Via Custom Admin Page

1. **Go to** `/billing/admin/free-access-page/`
2. **Single User Operations**:
   - Enter username or email
   - Choose access type (trial or lifetime)
   - Set trial days if applicable
   - Click "Grant Access" or "Revoke Access"
3. **Bulk Operations**:
   - Enter multiple users (one per line)
   - Choose access type and trial days
   - Click "Bulk Grant Access"

### Via API

```bash
# Grant lifetime free access
curl -X POST /billing/admin/grant-free-access/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{"user_identifier": "username", "access_type": "lifetime"}'

# Extend trial
curl -X POST /billing/admin/grant-free-access/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{"user_identifier": "email@example.com", "access_type": "trial", "trial_days": 60}'
```

### Via Management Command

```bash
# Grant lifetime free access to specific users
python manage.py grant_free_access --users user1 user2 --lifetime

# Extend trial for users in a file
python manage.py grant_free_access --file users.txt --trial-days 90

# Dry run to see what would happen
python manage.py grant_free_access --users user1 --lifetime --dry-run
```

## Access Types

### 1. Lifetime Free Access
- Sets `lifetime_free = True`
- Sets `status = 'ACTIVE'`
- User has permanent access without expiration

### 2. Trial Extension
- Extends `trial_end_at` by specified days
- User maintains trial access until new expiration date
- Default extension is 30 days

## Security

- All admin functions require staff privileges
- API endpoints check `user.is_staff` permission
- CSRF protection enabled for all forms
- Audit trail maintained through Django admin logs

## Bulk Operations

### File Format
Create a text file with one username or email per line:
```
user1
user2@example.com
user3
```

### Processing
- Bulk operations process users sequentially with 100ms delays
- Progress tracking and error reporting
- Automatic cleanup of input fields after completion

## Troubleshooting

### Common Issues

1. **User not found**: Check username/email spelling
2. **Permission denied**: Ensure user has staff privileges
3. **CSRF token error**: Refresh the page and try again

### Error Messages

- `User not found`: Username/email doesn't exist
- `No subscription found`: User has no subscription record
- `POST method required`: Wrong HTTP method used

## Examples

### Grant Lifetime Access to Beta Testers
```bash
python manage.py grant_free_access --users beta1 beta2 beta3 --lifetime
```

### Extend Trial for All Users
```bash
python manage.py grant_free_access --file all_users.txt --trial-days 14
```

### Single User via Admin Page
1. Go to `/billing/admin/free-access-page/`
2. Enter username: `john_doe`
3. Select: "Grant Lifetime Free"
4. Click: "Grant Access"

## Integration with Existing System

The free access features integrate seamlessly with your existing:
- Subscription model and billing system
- User authentication and permissions
- Promo code system
- Trial management

Users granted free access will automatically bypass subscription checks in your decorators and views.
