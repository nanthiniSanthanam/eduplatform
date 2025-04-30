# Step-by-Step Guide to Testing Your Educational Platform Locally

This guide will help you test your educational platform with all three user tiers:

1. Unregistered users: Can view basic content
2. Registered users: Can view intermediate content
3. Paid users: Can view advanced content with certificates

## Prerequisites

- VS Code installed on your computer
- Your educational platform code downloaded
- Python and Node.js installed

## Step 1: Open VS Code and Your Project

1. Open VS Code
2. Click on "File" → "Open Folder"
3. Navigate to `C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform`
4. Click "Select Folder"

## Step 2: Set Up the Backend

1. Open a terminal in VS Code:

   - Click "Terminal" in the top menu
   - Select "New Terminal"

2. Navigate to the backend directory and activate virtual environment:
   cd backend venv\Scripts\activate

3. Create test data (users and courses with different access levels):
   python manage.py setup_test_data

This will create:

- Admin user: admin@example.com / admin123
- Premium user: premium@example.com / premium123
- Basic user: basic@example.com / basic123
- Free user: free@example.com / free123
- Instructor: instructor@example.com / instructor123

4. Start the backend server in production-like mode:
   python manage.py run_local_prod

This will start your backend at http://127.0.0.1:8000/

## Step 3: Set Up the Frontend

1. Open another terminal in VS Code:

- Click the "+" icon in the terminal panel

2. Navigate to the frontend directory:
   cd frontend

3. Install dependencies (if needed):
   npm run dev

This will start your frontend at http://localhost:5173/

## Step 4: Test Different User Types

### Testing as an Unregistered User:

1. Open your browser and go to http://localhost:5173
2. Browse courses without logging in
3. You should only see basic content

### Testing as a Free Registered User:

1. Click "Login" and enter:

- Email: free@example.com
- Password: free123

2. Browse courses
3. You should now see intermediate content

### Testing as a Premium User:

1. Logout if currently logged in
2. Click "Login" and enter:

- Email: premium@example.com
- Password: premium123

3. Browse courses
4. You should see all content including premium resources
5. You should be able to get certificates

## Step 5: Stopping the Servers

When you're done testing:

1. Go to the VS Code terminal running the frontend
2. Press Ctrl+C to stop it
3. Go to the VS Code terminal running the backend
4. Press Ctrl+C to stop it

## Troubleshooting

- If you see an error about port already in use, try using a different port:
  python manage.py run_local_prod --port=8001

- If images or CSS aren't loading, make sure static files are collected:
  python manage.py collectstatic

- If login isn't working, make sure the backend is running properly

5. Testing Your Three User Tiers
   Now that both servers are running, open your browser to http://localhost:5173 to test:

As an Unregistered User:
Simply browse without logging in
You should only see basic content
As a Registered (Free) User:
Log in with: free@example.com / free123
You should now see intermediate content
As a Premium User:
Log in with: premium@example.com / premium123
You should see all content including premium resources
You should be able to get certificates
What These Files Do
settings_local_prod.py: Creates a version of your site that acts like a production site while running on your computer
run_local_prod.py: Makes it easy to start the production-like server
setup_test_data.py: Creates test users and content with different access levels
LOCAL_PROD_TESTING.md: A guide you can refer to whenever you need to test your site
Next Steps
Use this setup to thoroughly test how your educational platform handles the three user tiers
Make any necessary adjustments to your access control logic
When everything works correctly locally, you'll be ready for real hosting
