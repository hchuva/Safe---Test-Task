import argparse
import logging

from BackupHandler import BackupHandler

def main():

    parser = argparse.ArgumentParser(description="Backup utility")
    subparsers = parser.add_subparsers(help="Backup commands")

    backupStarter = subparsers.add_parser("start", help="Start the backup cycle")
    #backupStarter.add_argument("-c", "--config", help="Path to the config file")
    backupStarter.add_argument("-i", "--interval", help="Interval between backup cycles in seconds")
    backupStarter.add_argument("-b", "--backup", help="Backup directory")
    backupStarter.add_argument("-s", "--source", help="Source directory")
    backupStarter.add_argument("-a", "--algo", help="Hashing algorithm to use", default="md5")
    backupStarter.add_argument("-m", "--manager", help="Backup manager to use", default="fileSystem")

    args = parser.parse_args()
    args.backup = args.backup.rstrip("/")
    args.source = args.source.rstrip("/")

    logger = setupLogging()

    logger.info("Parsing config file")

    #configFile = configparser.ConfigParser()
    #configFile.read(args.config)

    logger.info("Backup interval was set to %s seconds" % args.interval)
    logger.info("Backup directory was set to %s" % args.backup)
    logger.info("Source directory was set to %s" % args.source)

    backupHandler = BackupHandler(float(args.interval), args.backup, args.source, args.algo, args.manager)

    logger.info("Starting continuous backup")
    try:
        backupHandler.run()
    except KeyboardInterrupt:
        logger.info("Continuous backup stopped")
    

def setupLogging():

    # Create a logger
    logger = logging.getLogger("backup")
    logger.setLevel(logging.DEBUG)

    # Create a console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create a file handler
    fh = logging.FileHandler("backup.log")
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