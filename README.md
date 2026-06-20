# MCQ Test Portal (Django Full-Stack)

A full-stack Python/Django web app for running MCQ tests:
- Admins upload questions via **Excel (.xlsx)**
- Students register, log in, and take timed tests
- **Tab-switch / fullscreen-exit detection** with warnings, auto-submitting the test after a configurable number of violations

---

## 1. Setup

```bash
cd mcq_app
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Open **http://127.0.0.1:8000/**

## 2. Creating an Admin account

There are two ways:

**Option A — via the website (easiest):**
1. Go to `/admin-signup/` (link is on the login page: "Admin sign up").
2. Enter the **Admin Signup Code**. By default it's `ADMIN-SETUP-2026`,
   set in `mcq_app/settings.py` as `ADMIN_SIGNUP_CODE`. **Change this value**
   before sharing the app with anyone.

**Option B — via command line:**
```bash
python manage.py createsuperuser
```

## 3. Admin workflow
1. Log in → you land on the **Admin Dashboard**.
2. Click **"+ Create Exam"** → set title, description, duration (minutes),
   and **max tab-switch violations allowed** before auto-submit.
3. You're redirected to **Upload Questions** for that exam.
4. Click **"Download Sample Template"** to get a correctly formatted `.xlsx`,
   or build your own with these column headers in the first row:

   | question_text | option_a | option_b | option_c | option_d | correct_option | marks |
   |---|---|---|---|---|---|---|
   | What is 2+2? | 3 | 4 | 5 | 6 | B | 1 |

   - `correct_option` must be `A`, `B`, `C`, or `D`.
   - `marks` is optional (defaults to 1 per question).
   - You can upload multiple files; new questions are appended.
5. Toggle the exam **Active/Inactive** from the dashboard — only active exams
   are visible to students.
6. Click **"Results"** on any exam to see every student's score, status, and
   number of recorded violations.

## 4. Student workflow
1. Register an account at `/register/`.
2. Dashboard shows all **active** exams. Click **"Start Test"**.
3. Click **"Start Test (Enter Fullscreen)"** — the test loads in fullscreen
   and the timer + tab-switch monitor begin.
4. Answer questions, then click **Submit Test**, or let the timer run out
   for auto-submission.

## 5. How tab-switch detection works

The test page listens for:
- `visibilitychange` → fires when the browser tab is minimized, switched, or the device is locked.
- `window blur` (only when the tab is still visible) → catches alt-tabbing to another application.
- `fullscreenchange` → fires if the student exits fullscreen.

Each event sends an AJAX request to the server, which increments
`violation_count` on the attempt and returns the updated count. The page shows
a warning modal each time. Once the count reaches **Max Violations** (set per
exam), the test is **auto-submitted** with whatever answers were filled in.

The app also:
- Disables right-click and the F11 shortcut during the test.
- Shows a native "leave site?" browser prompt if the student tries to navigate away.

### Known limitations (browser security restrictions — true for any web-based proctoring tool)
- A student could still bypass detection using browser developer tools, a
  second physical device, or by disabling JavaScript. There is no way to make
  a 100% tab-switch-proof web page; this implements the standard
  industry-grade detection used by most browser-based online exam portals.
- Rapid alt-tabbing might occasionally register as 1–2 violations instead of
  exactly 1 due to how `blur`/`visibilitychange` overlap — this is tuned to
  avoid double-counting but isn't pixel-perfect across all browsers.

## 6. Project structure

```
mcq_app/
├── manage.py
├── requirements.txt
├── mcq_app/          # Django project settings & URLs
├── accounts/         # Login / registration / admin-signup views
├── exam/             # Exam, Question, TestAttempt, ViolationLog models + views
│   ├── utils.py       # Excel parsing logic
│   └── templatetags/  # custom dict-lookup template filter
├── templates/
└── static/
```

## 7. Tech stack
- **Backend**: Django 5.x
- **Database**: SQLite (default; swap `DATABASES` in `settings.py` for Postgres/MySQL in production)
- **Excel parsing**: openpyxl
- **Frontend**: Django templates + Bootstrap 5 (via CDN) + vanilla JavaScript

## 8. Before deploying to production
- Change `SECRET_KEY` and `ADMIN_SIGNUP_CODE` in `mcq_app/settings.py`.
- Set `DEBUG = False` and configure `ALLOWED_HOSTS`.
- Switch to a production database and a real WSGI server (gunicorn, etc.) behind HTTPS — fullscreen API and some browser security features require a secure (https) context in real deployments.

## 9. Deploying for free on Render (permanent link)

The project is already configured for this (`Procfile`, `requirements.txt`,
`whitenoise` for static files, Postgres support via `DATABASE_URL`). Steps:

1. **Push the project to GitHub.**
   ```bash
   cd mcq_app
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```

2. **Create a free Postgres database on Render.**
   - Go to https://render.com → sign up/log in (GitHub login is easiest).
   - Dashboard → **New** → **PostgreSQL** → choose the free plan → Create.
   - Once created, copy the **Internal Database URL** shown on its page.

3. **Create the web service.**
   - Dashboard → **New** → **Web Service** → connect your GitHub repo.
   - Settings:
     - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
     - **Start Command:** `gunicorn mcq_app.wsgi --log-file -`
     - **Instance Type:** Free
   - Under **Environment**, add these variables:
     | Key | Value |
     |---|---|
     | `SECRET_KEY` | any long random string |
     | `DEBUG` | `False` |
     | `ALLOWED_HOSTS` | `your-app-name.onrender.com` |
     | `ADMIN_SIGNUP_CODE` | a private code only you know |
     | `DATABASE_URL` | paste the Postgres URL from step 2 |
   - Click **Create Web Service**. Render will build and deploy automatically.

4. **First-time database setup.**
   The `Procfile`'s `release: python manage.py migrate` line runs
   migrations automatically on every deploy. If you ever need to run it
   manually, use the **Shell** tab on your Render service page:
   ```bash
   python manage.py migrate
   ```

5. **Get your link.**
   Render gives you a permanent URL like:
   `https://your-app-name.onrender.com`
   Share that with students and admins directly.

   > Free-tier services on Render "spin down" after 15 minutes of no
   > traffic and take ~30–50 seconds to wake back up on the next visit.
   > That's normal for the free plan — it doesn't lose any data.

### Alternative: PythonAnywhere (also free, simpler for SQLite, no spin-down)
- Sign up at https://www.pythonanywhere.com (free "Beginner" account).
- Upload your project (via their "Files" tab or `git clone` in a Bash console).
- Go to the **Web** tab → **Add a new web app** → Manual configuration → Django.
- Point the WSGI file to `mcq_app.wsgi.application` and set the virtualenv
  with `pip install -r requirements.txt --break-system-packages`.
- Run `python manage.py migrate` in their Bash console.
- Your link will be `https://<your-username>.pythonanywhere.com` — always on, no spin-down, but the free plan only allows that one fixed subdomain (no custom domain).

