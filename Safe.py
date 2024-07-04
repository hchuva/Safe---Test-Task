import argparse
import logging

from BackupHandler import BackupHandler

def main():

    parser = argparse.ArgumentParser(description="Backup utility")
    subparsers = parser.add_subparsers(help="Backup commands", required=True, dest="command")

    backupStarter = subparsers.add_parser("start", help="Start the backup cycle")
    backupStarter.add_argument("-i", "--interval", help="Interval between backup cycles in seconds", default=600, type=float)
    backupStarter.add_argument("-b", "--backup", help="Backup directory", required=True)
    backupStarter.add_argument("-s", "--source", help="Source directory", required=True)
    backupStarter.add_argument("-a", "--algo", help="Hashing algorithm to use", default="md5", choices=["md5", "sha256", "sha512"])
    backupStarter.add_argument("-m", "--manager", help="Backup manager to use", default="fileSystem", choices=["fileSystem"])
    backupStarter.add_argument("-l", "--log", help="Log file", default="safe.log")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        exit(1)

    args.backup = args.backup.rstrip("/")
    args.source = args.source.rstrip("/")

    logger = setupLogging(args.log)

    logger.info("Parsing config file")

    logger.info("Backup interval was set to %s seconds" % args.interval)
    logger.info("Backup directory was set to %s" % args.backup)
    logger.info("Source directory was set to %s" % args.source)

    backupHandler = BackupHandler(args.interval, args.backup, args.source, args.algo, args.manager)

    logger.info("Starting continuous backup")
    try:
        backupHandler.run()
    except KeyboardInterrupt:
        logger.info("Continuous backup stopped")
    

def setupLogging(logFile: str):

    # Create a logger
    logger = logging.getLogger("backup")
    logger.setLevel(logging.DEBUG)

    # Create a console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create a file handler
    fh = logging.FileHandler(logFile)
    fh.setLevel(logging.DEBUG)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add the formatter to the handlers
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

if __name__ == "__main__":
    main()



# For each file in source:
# IF exists in backup and hash is the same -> File did not change -> do nothing
# IF exists in backup and hash is different: -> File was modified -> update backup
# IF does not exist in backup -> File is new -> add to backup
# IF exists in backup but not in source -> File was deleted -> remove from backup