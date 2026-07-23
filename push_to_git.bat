@echo off
echo ========================================================
echo Pushing ShopBack codebase to GitHub...
echo Repository: https://github.com/kennethxkie123-cpu/shopback.git
echo ========================================================

IF NOT EXIST .git (
    echo Initializing Git repository...
    git init
    git branch -M main
    git remote add origin https://github.com/kennethxkie123-cpu/shopback.git
)

echo Adding files to staging...
git add .

echo Committing files...
git commit -m "ShopBack release: production security, subtabs, and Railway deployment readiness"

echo Setting remote URL...
git remote set-url origin https://github.com/kennethxkie123-cpu/shopback.git

echo Pushing to main branch on GitHub...
git push -u origin main

echo ========================================================
echo Done! Code pushed to GitHub successfully.
echo ========================================================
pause
