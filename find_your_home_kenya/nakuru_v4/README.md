# 🏠 Find Your Home Kenya

A full-featured house hunting platform built for Nakuru, Kenya.
- **Tenants** pay KSh 100 once → browse all listings
- **Landlords** pay KSh 300 once → post unlimited properties
- **Admin** controls everything from a hidden dashboard

---

## 📁 Project Structure

```
nakuru_houses/
├── nakuru_houses/         ← Django settings, URLs, utils
├── admin_panel/           ← Your private admin (hidden URL)
├── landlords/             ← Landlord section
├── tenants/               ← House hunter section
├── payments/              ← M-Pesa integration
├── static/                ← CSS, JS, images
├── media/                 ← User uploaded photos
├── manage.py
├── requirements.txt
└── .env                   ← Your secret config
```

---

## ⚙️ Setup Instructions

### 1. Install Python & pip
```bash
python --version   # needs Python 3.10+
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your `.env` file
Edit `.env` and set:
```
SECRET_KEY=generate-a-long-random-string
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_strong_password
ADMIN_EMAIL=your_email@gmail.com
MPESA_TILL_NUMBER=your_till_number
LANDLORD_FEE=300
TENANT_FEE=100

# For M-Pesa STK Push (optional - manual payment works without this):
MPESA_CONSUMER_KEY=from_safaricom_developer_portal
MPESA_CONSUMER_SECRET=from_safaricom_developer_portal
MPESA_SHORTCODE=your_till_or_paybill
MPESA_PASSKEY=from_safaricom
MPESA_ENV=sandbox   # change to 'production' when going live
```

### 5. Run database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create the admin account
```bash
python manage.py create_admin
```

### 7. Collect static files
```bash
python manage.py collectstatic
```

### 8. Run the server
```bash
python manage.py runserver
```

---

## 🔐 Accessing the Admin Panel

Your admin URL is **hidden**. By default it is:
```
http://localhost:8000/control-hub-x9z/
```

To change the admin URL path, set `ADMIN_SECRET_PATH` in your `.env`:
```
ADMIN_SECRET_PATH=my-secret-path-here
```

Then access: `http://yourdomain.com/my-secret-path-here/`

**No one will find this URL** — it's not linked anywhere on the site.

---

## 💳 M-Pesa Integration

### How payments work:
1. User clicks Pay → System sends STK Push to their phone
2. User enters M-Pesa PIN → Safaricom confirms payment
3. Account activates automatically

### If STK Push isn't set up yet:
- The system falls back to **manual payment entry**
- User sends money to your till number manually
- User enters their M-Pesa code
- Account activates after code entry

### To enable full STK Push:
1. Register at [Safaricom Developer Portal](https://developer.safaricom.co.ke/)
2. Create an app → get Consumer Key & Secret
3. Add credentials to your `.env`

---

## 🌐 Deployment (Going Live)

### Using PythonAnywhere (easiest & affordable):
1. Sign up at pythonanywhere.com
2. Upload your project
3. Set `DEBUG=False` in `.env`
4. Set `ALLOWED_HOSTS=yourdomain.com`
5. Configure your WSGI file to point to `nakuru_houses.wsgi`

### Important for production:
```
DEBUG=False
ALLOWED_HOSTS=nakuruhouses.com,www.nakuruhouses.com
```

---

## 📋 User Flows

### Tenant (House Hunter):
```
Visit site → Read landing page → Create account
→ Pay KSh 100 → Account active → Browse all listings
→ Search by type/location → View property details
→ Call/WhatsApp landlord directly
```

### Landlord:
```
Register → Pay KSh 300 → Dashboard unlocked
→ Post property (fill details + upload photos)
→ Admin reviews → Property goes live
→ Tenants contact you directly
```

### Admin (You):
```
Visit /control-hub-x9z/ → Login
→ Dashboard: see all stats
→ Approve/reject property listings
→ Manage landlord & tenant accounts
→ View all payments & revenue
→ Change M-Pesa till number anytime
→ Post properties directly
```

---

## 🎨 Design

- **Color scheme**: Dark navy (`#050d1a`) with electric cyan (`#00e5ff`)
- **Fonts**: Syne (headings) + DM Sans (body)
- **Icons**: Font Awesome 6
- Fully responsive (mobile-friendly)

---

## 🔧 Changing the Till Number

1. Go to your admin panel: `/control-hub-x9z/`
2. Click **Settings & Till No.**
3. Enter your new M-Pesa till number
4. Click **Save Settings**

The new till number appears on all payment pages instantly.

---

*Built for Nakuru. No agents. No hidden fees.*
