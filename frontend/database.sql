BEGIN TRANSACTION ;

CREATE TABLE status (
  name  text(10) primary key,
  value text(32)
  ) ;

CREATE TABLE users (
  username      text(20) primary key,
  password      text(20),
  changepw      integer(1),
  level         integer(1),
  email         text,
  token         text,
  expiry        text
  );

INSERT INTO "users" VALUES('admin', 'admin', 0, 9, 'd.brooks@auckland.ac.nz', '', '') ;
INSERT INTO "users" VALUES('guest', 'guest', 0, 1, '',                        '', '') ;

COMMIT ;

