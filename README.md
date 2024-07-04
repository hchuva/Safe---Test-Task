# Safe Test-Task

A simple directory replication tool made as a test task.

## Usage:

`python3 safe.py start [-i INTERVAL] [-b BACKUP] [-s SOURCE] [-a ALGO] [-m MANAGER] [-l LOG]`


INTERVAL:
 - Interval between backup cycles in seconds
 - Defaults to 10 minutes (600 seconds)

BACKUP:
 - Path for file backups

SOURCE:
 - Path of files to backup

ALGO:
 - Hashing algorithm to use
 - Possible values: md5, sha256, sha512
 - Defaults to: md5

MANAGER:
 - Backup manager to use (file system, database, etc)
 - Possible values: fileSystem
 - Defaults to: fileSystem

LOG:
 - Log file path
 - Defaults to: safe.log