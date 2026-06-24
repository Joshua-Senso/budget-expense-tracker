#!/usr/bin/env bash
# pg_dump the database and push the dump to object storage (R2 in prod, MinIO in
# dev). Captures Better Auth + application schemas together (one database).
# Intended to be run on a schedule by the worker/host; see ARCHITECTURE.md §11.
#
# Required env: DATABASE_URL, S3_ENDPOINT_URL, S3_ACCESS_KEY_ID,
#               S3_SECRET_ACCESS_KEY, BACKUPS_BUCKET
set -euo pipefail

: "${DATABASE_URL:?set DATABASE_URL}"
: "${BACKUPS_BUCKET:?set BACKUPS_BUCKET}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DUMP="/tmp/expense-${STAMP}.sql.gz"

echo "backup: dumping database -> ${DUMP}"
pg_dump "${DATABASE_URL}" | gzip > "${DUMP}"

# TODO: upload with the AWS/S3 CLI or mc, e.g.
#   aws --endpoint-url "${S3_ENDPOINT_URL}" s3 cp "${DUMP}" "s3://${BACKUPS_BUCKET}/"
echo "backup: TODO upload ${DUMP} to ${BACKUPS_BUCKET}"
