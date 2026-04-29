#!/bin/bash
cd "/Users/apple/Desktop/new/schoollistinh"

# Clear any cached configs
rm -f bootstrap/cache/*.php 2>/dev/null

echo "=== ARTISAN VERSION ===" > /tmp/setup_log.txt
php artisan --version >> /tmp/setup_log.txt 2>&1

echo "=== CHECK ENV CACHE DRIVER ===" >> /tmp/setup_log.txt
grep "CACHE" .env >> /tmp/setup_log.txt 2>&1

echo "=== SYNC JSON ===" >> /tmp/setup_log.txt
php artisan schools:sync-json >> /tmp/setup_log.txt 2>&1
EXIT_CODE=$?
echo "=== EXIT CODE: $EXIT_CODE ===" >> /tmp/setup_log.txt

cat /tmp/setup_log.txt
