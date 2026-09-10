@echo off
echo Choose an option:
echo 0. git pull
echo 1. Deploy with migrate 
echo 2. Deploy without migrate and collectstatic
echo 3. Only collectstatic
echo 4. Install requirements.txt
echo 5. debug portal.service; app-django
echo 6. debug django-q.service
echo 7. project ambient .venv active
echo 8. Prepare origin/main (without migrate)
echo 9. Deploy origin/main with migrate

set /p option="Enter option number (0-9): "

if "%option%"=="0" (
    echo Connecting to server...
    ssh farol "cd /var/www/portal; source .venv/bin/activate; git pull; journalctl -u portal.service -f"
    echo completed successfully!
)

if "%option%"=="1" (
    echo Starting deployment with database migration...
    echo Connecting to server...
    ssh farol "cd /var/www/portal; source .venv/bin/activate; git pull; python manage.py migrate; systemctl restart portal.service; systemctl restart scheduler.service; journalctl -u portal.service -f"
    echo Deployment with migration completed successfully!
)

if "%option%"=="2" (
    echo Starting deployment without migration...
    echo Connecting to server...
    ssh farol "cd /var/www/portal; source .venv/bin/activate; git pull; systemctl restart portal.service; systemctl restart scheduler.service; python manage.py collectstatic; journalctl -u portal.service -f"
    echo Deployment completed successfully!
)

if "%option%"=="3" (
    echo Starting collectstatic operation...
    echo Connecting to server...
    ssh farol "cd /var/www/portal; source .venv/bin/activate; git pull; python manage.py collectstatic; journalctl -u portal.service -f"
    echo Collectstatic operation completed successfully!
)

if "%option%"=="4" (
    echo Starting requirements.txt operation...
    echo Connecting to server...
    ssh farol "cd /var/www/portal; source .venv/bin/activate; git pull; pip install -r requirements.txt; systemctl restart portal.service; systemctl restart scheduler.service; bash"
    echo Requirements.txt operation completed successfully!
)

if "%option%"=="5" (
    echo Starting DEBUG portal.Service...
    echo Connecting to server...
    ssh farol "cd /var/www/portal; source .venv/bin/activate; journalctl -u portal.service -f"
    echo DEBUG portal.Service completed successfully!
)

if "%option%"=="6" (
    echo Starting DEBUG portal.Service...
    echo Connecting to server...
    ssh farol "cd /var/www/portal; source .venv/bin/activate; journalctl -u  scheduler.service -f"
    echo DEBUG portal.Service completed successfully!
)

if "%option%"=="8" (
    echo Preparing production checkout from origin/main...
    echo Connecting to server...
    ssh farol "set -e; cd /var/www/portal; source .venv/bin/activate; git fetch origin main; git checkout main; git pull --ff-only origin main; python manage.py check; python manage.py makemigrations --check --dry-run; echo Active commit:; git rev-parse HEAD; python manage.py showmigrations --plan"
    echo Preparation completed successfully!
)

if "%option%"=="9" (
    echo Deploying origin/main with database migration...
    echo Connecting to server...
    ssh farol "set -e; cd /var/www/portal; source .venv/bin/activate; git fetch origin main; git checkout main; git pull --ff-only origin main; python manage.py check; python manage.py makemigrations --check --dry-run; python manage.py migrate; python manage.py collectstatic --noinput; systemctl restart portal.service; systemctl restart scheduler.service; systemctl is-active portal.service scheduler.service; echo Active commit:; git rev-parse HEAD"
    echo Deployment completed successfully!
)

@REM touch /var/www/portal/portal/wsgi.py - do not restart service.
