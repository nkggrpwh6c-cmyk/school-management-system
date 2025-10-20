# 🔐 RENDER SECURITY SETUP GUIDE
**Critical Environment Variables for Production**

---

## ⚠️ IMMEDIATE ACTION REQUIRED

These environment variables MUST be set in Render for production security.

---

## 📝 STEP-BY-STEP SETUP

### 1. Access Render Environment Settings
1. Go to https://dashboard.render.com
2. Click on your service: **vbcasms**
3. Click **Environment** in the left sidebar
4. You'll see the environment variables section

---

### 2. Add These Environment Variables

Click **Add Environment Variable** for each of these:

#### A. SECRET_KEY (CRITICAL)
```
Key: SECRET_KEY
Value: [Generate a random 64-character string]
```

**How to generate SECRET_KEY:**
- Go to: https://djecrety.ir/
- Copy the generated key
- Paste as value

**OR use this Python command:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

#### B. DEBUG
```
Key: DEBUG
Value: False
```
✅ **Must be False in production** - Never set to True

---

#### C. ALLOWED_HOSTS
```
Key: ALLOWED_HOSTS
Value: vbcasms.onrender.com,.onrender.com
```
✅ Restricts which domains can access your site

---

#### D. CSRF_TRUSTED_ORIGINS
```
Key: CSRF_TRUSTED_ORIGINS
Value: https://vbcasms.onrender.com
```
✅ Protects against CSRF attacks

---

#### E. DATABASE_URL
```
Key: DATABASE_URL
Value: [Your Supabase connection string]
```
✅ Already set - verify it's the pooler URL

---

#### F. SECURE_SSL_REDIRECT
```
Key: SECURE_SSL_REDIRECT
Value: True
```
✅ Forces all connections to use HTTPS

---

#### G. CSRF_COOKIE_SECURE
```
Key: CSRF_COOKIE_SECURE
Value: True
```
✅ CSRF cookies only sent over HTTPS

---

#### H. SESSION_COOKIE_SECURE
```
Key: SESSION_COOKIE_SECURE
Value: True
```
✅ Session cookies only sent over HTTPS

---

### 3. Save and Deploy
1. After adding all variables, click **Save Changes**
2. Render will automatically redeploy
3. Wait 2-3 minutes for deployment to complete

---

## ✅ VERIFICATION CHECKLIST

After deployment, verify these:

### Test 1: HTTPS Redirect
- [ ] Go to http://vbcasms.onrender.com (http not https)
- [ ] Should automatically redirect to https://

### Test 2: Login Security
- [ ] Try logging in with wrong password 5 times
- [ ] Should be locked out for 30 minutes

### Test 3: Session Timeout
- [ ] Log in successfully
- [ ] Wait 30 minutes without activity
- [ ] Should be automatically logged out

### Test 4: CSRF Protection
- [ ] Open browser console (F12)
- [ ] Try submitting a form without CSRF token
- [ ] Should be blocked with error

---

## 🔒 ADDITIONAL SECURITY SETTINGS (Optional but Recommended)

### Email Notifications (for password resets)
```
Key: EMAIL_HOST
Value: smtp.gmail.com

Key: EMAIL_PORT
Value: 587

Key: EMAIL_HOST_USER
Value: your-school-email@gmail.com

Key: EMAIL_HOST_PASSWORD
Value: [App-specific password from Gmail]

Key: EMAIL_USE_TLS
Value: True

Key: DEFAULT_FROM_EMAIL
Value: noreply@vbca.edu
```

**Note:** For Gmail, create an App Password:
1. Go to Google Account settings
2. Security → 2-Step Verification
3. App passwords → Generate new
4. Use that password (not your regular password)

---

### Session Settings (Already configured, but can customize)
```
Key: SESSION_COOKIE_AGE
Value: 1800
(30 minutes in seconds - adjust if needed)

Key: LOGIN_ATTEMPTS_LIMIT
Value: 5
(Number of login attempts before lockout)

Key: ACCOUNT_LOCKOUT_DURATION
Value: 1800
(Lockout duration in seconds - 30 minutes)
```

---

## 🚨 CRITICAL: Change Default Passwords

After setting environment variables, immediately change these:

### Admin Account
- Current: `admin` / `admin123`
- **Change to:** Strong password (12+ characters)

### Registrar Account
- Current: `crenz` / `crenz123`
- **Change to:** Strong password (12+ characters)

**How to Change:**
1. Log in to https://vbcasms.onrender.com
2. Click profile/username in top right
3. Click "Change Password"
4. Enter new strong password
5. Save

**Strong Password Requirements:**
- Minimum 12 characters
- Mix of uppercase and lowercase
- Include numbers
- Include special characters (@, #, $, %, etc.)
- Not a common word or phrase
- Not similar to username

**Example Strong Passwords:**
- `Vbca$2024!Secure#Reg`
- `MySchool@Reg2024#Safe`
- `SecureVBCA!2024$Pass`

---

## 📊 CURRENT ENVIRONMENT VARIABLES

After setup, you should have these variables:

```
DATABASE_URL = postgresql://postgres:...@...pooler.supabase.com:6543/postgres
SECRET_KEY = django-insecure-xxx... (MUST CHANGE THIS)
DEBUG = False
ALLOWED_HOSTS = vbcasms.onrender.com,.onrender.com
CSRF_TRUSTED_ORIGINS = https://vbcasms.onrender.com
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

---

## 🔧 TROUBLESHOOTING

### Issue: "Bad Request (400)" after setting ALLOWED_HOSTS
**Solution:** Make sure CSRF_TRUSTED_ORIGINS includes `https://`

### Issue: Site won't load after setting SECURE_SSL_REDIRECT
**Solution:** Wait 2-3 minutes for deployment, then try https:// (not http://)

### Issue: Login not working after security changes
**Solution:** 
1. Clear browser cache
2. Try incognito/private window
3. Check if cookies are enabled

### Issue: Can't access admin after password change
**Solution:**
1. Try logging in with new password
2. Wait 30 minutes if locked out
3. Contact system admin if still locked

---

## 📞 EMERGENCY ACCESS

If you get locked out:

### Option 1: Wait for Lockout to Expire
- Lockouts expire after 30 minutes
- Try logging in again after timeout

### Option 2: Reset via Render Shell (if available on paid plan)
```bash
python manage.py changepassword admin
```

### Option 3: Create New Admin (if critically needed)
```bash
python manage.py createsuperuser
```

---

## 📈 MONITORING

### Check Security Logs
1. Render → Logs tab
2. Look for:
   - Failed login attempts
   - Security warnings
   - HTTPS redirects
   - CSRF errors

### Security Headers Check
Visit: https://securityheaders.com/?q=https://vbcasms.onrender.com
- Should get an A or A+ rating

---

## ✅ FINAL CHECKLIST

Before going live with student data:

- [ ] All environment variables set
- [ ] SECRET_KEY changed from default
- [ ] DEBUG = False
- [ ] HTTPS redirect working
- [ ] Default passwords changed
- [ ] Login lockout tested
- [ ] Session timeout tested
- [ ] CSRF protection verified
- [ ] Security headers checked
- [ ] Backup system tested
- [ ] Staff trained on security practices

---

## 📚 REFERENCES

- Django Security Docs: https://docs.djangoproject.com/en/4.2/topics/security/
- Render Environment Variables: https://render.com/docs/environment-variables
- OWASP Top 10: https://owasp.org/www-project-top-ten/

---

**IMPORTANT:** Keep this document secure and accessible only to authorized IT staff.

**Last Updated:** October 20, 2025

