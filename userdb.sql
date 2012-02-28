PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (username TEXT PRIMARY KEY, password TEXT, changepw INTEGER, level INTEGER);
INSERT INTO "users" VALUES('admin','admin',0,9);
COMMIT;
