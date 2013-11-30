#!/bin/bash

echo $1


DJ_APPS="wom_classification wom_pebbles wom_river wom_user"


if [ $1 == reset ]; then
    echo "Cleanup past migrations"    
    for app_name in $DJ_APPS; do
        migration_path=./$app_name/migrations
        if [ -d $migration_path ]; then
            rm -r $migration_path
        fi
    done
    echo "Initialize the migration data"
    for app_name in $DJ_APPS; do
        python manage.py schemamigration $app_name --initial
    done
    if [ -f ./db.sql3 ]; then
        echo "Remove db.sql3"
        # Just in case we're using a local sql3 db, remove it for
        # proper reset (in other cases, cleaning out the db must be
        # done before calling this script)
        rm ./db.sql3
    fi
    echo "Setup the base db"
    python manage.py syncdb
    echo "Apply migrations"
    python manage.py migrate
else
    # Sync the db
    python manage.py syncdb
    # Apply the migration
    python manage.py migrate
fi    

