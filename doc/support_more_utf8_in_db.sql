
-- Truncated text (typically in post/pebble description) can be due to
-- the db's encoding not supporting the full range of utf-8 characters
-- (typically emojis) which requires changing the character set.
--
-- See https://mathiasbynens.be/notes/mysql-utf8mb4#column-index-length

-- Also the Django app settings should have something like:
--  DATABASES = {
--     'default': {
--       'ENGINE': 'django.db.backends.mysql',
--       'NAME': '...',     # Irrelevant to encoding
--       'USER': '...',     # Irrelevant to encoding
--       'PASSWORD': '...', # Irrelevant to encoding
--       'HOST': '...',     # Irrelevant to encoding
--       'PORT': '',        # Irrelevant to encoding
--       'STORAGE_ENGINE': 'INNODB', # Force storage engine, unrelated to encoding but better for consistency over stack updates (see https://stackoverflow.com/questions/6178816/django-cannot-add-or-update-a-child-row-a-foreign-key-constraint-fails)
--       'OPTIONS': { # Here the actual encoding declaration
--         'charset': 'utf8mb4',
--         'use_unicode': True,
--         }
--     }
-- }


-- For each database:
ALTER DATABASE tibonihoo_wom CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
--
ALTER TABLE django_admin_log CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE django_admin_log MODIFY change_message longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE wom_classification_tag CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE wom_classification_tag MODIFY name varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE wom_pebbles_reference CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE wom_pebbles_reference MODIFY url varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE wom_pebbles_reference MODIFY title varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE wom_pebbles_reference MODIFY description longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE wom_river_webfeed CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE wom_river_webfeed MODIFY xmlURL varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE wom_tributary_generatedfeed CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE wom_tributary_generatedfeed MODIFY title varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
ALTER TABLE wom_user_userbookmark CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE wom_user_userbookmark MODIFY comment longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

REPAIR TABLE django_admin_log;
OPTIMIZE TABLE django_admin_log;
REPAIR TABLE wom_classification_tag;
OPTIMIZE TABLE wom_classification_tag;
REPAIR TABLE wom_pebbles_reference;
OPTIMIZE TABLE wom_pebbles_reference;
REPAIR TABLE wom_river_webfeed;
OPTIMIZE TABLE wom_river_webfeed;
REPAIR TABLE wom_tributary_generatedfeed;
OPTIMIZE TABLE wom_tributary_generatedfeed;
REPAIR TABLE wom_user_userbookmark;
OPTIMIZE TABLE wom_user_userbookmark;
