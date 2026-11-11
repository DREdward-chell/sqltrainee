#!/bin/sh
set -eu
export PGPASSWORD="$(cat /var/lib/sqltrainee/work/.reader-password)"
exec psql -X -h 127.0.0.1 -p 5432 -U sqltrainee -d sqltrainee "$@"
