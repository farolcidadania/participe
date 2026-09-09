# Deploy em produção

A produção usa `/var/www/portal`, `portal.service`, `scheduler.service` e
`/var/www/portal/.venv`. O domínio, `.env`, banco e mídia são preservados.

## Pré-voo

```bash
ssh farol
cd /var/www/portal
git status --short --branch
git remote -v
git rev-parse HEAD
systemctl is-active portal.service scheduler.service
systemctl cat portal.service scheduler.service
```

Antes da troca, faça backup fora do checkout:

```bash
set -a
source .env
set +a
STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP=/var/backups/farol/$STAMP
mkdir -p "$BACKUP"
git rev-parse HEAD > "$BACKUP/commit.txt"
cp .env "$BACKUP/.env"
tar -czf "$BACKUP/media.tar.gz" media 2>/dev/null || true
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USERNAME:-$POSTGRES_USER}" -d "${POSTGRES_DATABASE:-$POSTGRES_DB}" --format=custom --file="$BACKUP/database.dump"
```

## Troca controlada

O commit de compatibilidade deve estar publicado em
`farolcidadania/participe` antes desta etapa:

```bash
cd /var/www/portal
source .venv/bin/activate
git fetch origin main
git checkout main
git pull --ff-only origin main
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations --plan
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart portal.service
systemctl restart scheduler.service
systemctl is-active portal.service scheduler.service
```

Não aceite migrações que recriem tabelas do app `camera` ou alterem o campo
existente `camera_id`. O histórico deve continuar usando `camera`, não
`camara`.

## Pós-validação

```bash
journalctl -u portal.service -n 100 --no-pager
journalctl -u scheduler.service -n 100 --no-pager
systemctl list-units --type=service --all | grep -Ei 'scheduler|portal'
```

Valide o domínio atual, login, estáticos e uma execução controlada do scraper.
Deve existir somente uma instância de `scheduler.service`.

## Rollback

```bash
cd /var/www/portal
systemctl stop scheduler.service portal.service
git checkout "$(cat /var/backups/farol/<STAMP>/commit.txt)"
cp /var/backups/farol/<STAMP>/.env .env
systemctl start portal.service scheduler.service
systemctl is-active portal.service scheduler.service
```

Restaure o `database.dump` somente se uma alteração incompatível tiver sido
aplicada ao banco.
