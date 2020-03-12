#!/bin/bash
/opt/odoo/server/odoo.py \
-c /opt/odoo/config/odoo-server.conf \
--db_host=$DB_PORT_5432_TCP_ADDR
exec "$@"