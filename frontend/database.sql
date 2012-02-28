BEGIN TRANSACTION;

CREATE TABLE status (
  name  text(10) primary key,
  value text(32)
  ) ;

CREATE TABLE users (
  username      text(20) primary key,
  password      text(20),
  changepw      integer(1),
  level         integer(1)
  );
INSERT INTO "users" VALUES('admin','admin',0,9);

COMMIT;

