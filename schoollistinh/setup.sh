#!/bin/bash
cd "/Users/apple/Desktop/new/schoollistinh"
php artisan --version > /tmp/setup.log 2>&1
echo "---" >> /tmp/setup.log
php artisan config:clear >> /tmp/setup.log 2>&1
echo "---" >> /tmp/setup.log
php artisan schools:sync-json >> /tmp/setup.log 2>&1
echo "---EXIT:$?" >> /tmp/setup.log
cat /tmp/setup.log
