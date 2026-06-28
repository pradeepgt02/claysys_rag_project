@echo off
echo Pushing project to https://github.com/pradeepgt02/claysys_rag_project...
git add .
git commit -m "Initialize project and push to github"
git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/pradeepgt02/claysys_rag_project.git
git push -u origin main
echo.
echo Process complete. If git requested credentials, please authenticate in the popup.
pause
