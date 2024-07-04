import time
import os
import logging
from configparser import ConfigParser
from HashGenerators import MD5Generator, SHA256Generator, SHA512Generator
from FileHandler import FileSystemHandler

logger = logging.getLogger('SAFE')

class BackupHandler:

    hashingAlgorithms = {
        "md5": MD5Generator,
        "sha256": SHA256Generator,
        "sha512": SHA512Generator
    }

    backupStrategies = {
        "fileSystem": FileSystemHandler,
    }

    def __init__(self, backupInterval: int, backupPath: str = "", sourcePath: str = "", hashAlgorithm: str = "md5", backupStrategy: str = "fileSystem"):
        logger.info("Initializing Backup Handler")

        self.backupInterval = backupInterval
        self.backupPath = backupPath
        self.sourcePath = sourcePath
        self.hashAlgorithm = self.__getHashingAlgorithm(hashAlgorithm)
        self.backupStrategy = self.__getBackupStrategy(backupStrategy)

        # Create the dictionary that will store and track the backup data
        self.__readBackup()

        # Create the tim tracking variable
        self.lastBackup = time.time()

    def __getHashingAlgorithm(self, hashType: str):
        if hashType not in self.hashingAlgorithms:
            logger.warn("Invalid hash type %s. Defaulting to md5", hashType)
            return self.hashingAlgorithms["md5"]
        return self.hashingAlgorithms[hashType]
    
    def __getBackupStrategy(self, strategy: str):
        if strategy not in self.backupStrategies:
            logger.warn("Invalid backup strategy %s. Defaulting to fileSystem", strategy)
            return self.backupStrategies["fileSystem"]
        return self.backupStrategies[strategy]
    
    def run(self):

        logger.info("Backup Handler started")
        logger.info("Executing initial backup")
        self.__backupSource()

        logger.info("Starting continuous backup. Backup interval is %s seconds", self.backupInterval)
        while True:
            if time.time() - self.lastBackup >= self.backupInterval:
                logger.info("Starting a new backup")
                self.lastBackup = time.time()
                self.__backupSource()

    def __readBackup(self):
        # Lets first get all the files in the backup directory
        fileList = self.backupStrategy.Walk(self.backupPath)

        # Now lets open each file and hash it
        self.backupDict = self.__hashFileList(fileList, self.backupPath)

    def __hashFileList(self, fileList: dict, path: str):
        
        for file in fileList:
            fileData, _ = self.backupStrategy.ReadFile(path + "/" + file)
            hashedData = self.hashAlgorithm.hashFile(fileData)
            fileList[file]["hash"] = hashedData

        return fileList
    
    def __writeBackup(self, filesToBackup: dict, sourceDict: dict):
        totalFileChange = [0,0]
        for i in filesToBackup["newFiles"]:
            # Load the source file
            currFileData, currFileSize = self.backupStrategy.ReadFile(self.sourcePath + "/" + i)

            totalFileChange[0] += currFileSize
            logger.info("Creating new file: %s | Size: %skb", i, str(currFileSize))
            # Write the source file to the backup
            self.backupStrategy.CreateFile(self.backupPath + sourceDict[i]['path'], sourceDict[i]['file'], currFileData)

            self.backupDict[i] = sourceDict[i]
        
        for i in filesToBackup["modifiedFiles"]:
            # Load the source file
            currFileData, currFileSize = self.backupStrategy.ReadFile(self.sourcePath + "/" + i)

            totalFileChange[0] += currFileSize
            logger.info("Modifying file: %s | Size: %skb", i, str(currFileSize))
            # Write the source file to the backup
            self.backupStrategy.SaveFile(self.backupPath + sourceDict[i]['path'], sourceDict[i]['file'], currFileData, True)

            self.backupDict[i] = sourceDict[i]
        
        for i in filesToBackup["deletedFiles"]:
            currFileSize = self.backupStrategy.GetFileSize(self.backupPath + "/" + i)
            totalFileChange[1] += currFileSize
            logger.info("Deleting file: %s | Size: %skb", i, str(currFileSize))
            self.backupStrategy.DeleteFile(self.backupPath + "/" + i)
            self.backupDict.pop(i)

        # Do some cleanup, because its likely we will end up with empty folders
        for dir in self.backupStrategy.GetEmptyDirectories(self.backupPath):
            logger.info("Deleting empty directory: %s", dir)
            self.backupStrategy.DeleteDirectory(dir)

        return totalFileChange
    
    def __backupSource(self):

        backupStartTime = time.time()

        sourceDict = {}

        # Lets first get all the files in the source directory
        fileList = self.backupStrategy.Walk(self.sourcePath)

        # Now lets open each file and hash it
        sourceDict = self.__hashFileList(fileList, self.sourcePath)

        # sourceKeys is a list of all the keys in the sourceDict
        sourceKeys = set(sourceDict.keys())

        # backupKeys is a list of all the keys in the backupDict
        backupKeys = set(self.backupDict.keys())

        # Find keys that are in the source but not in the backup. These files are new and must be backed up
        newFiles = sourceKeys - backupKeys
        for file in newFiles:
            logger.info("New file found: %s", file)

        # Find keys that are in the source and in the backup. These files may have been modified, so we must compare hashes to know if they were modified and must be backed up
        commonFiles = sourceKeys & backupKeys

        # Find keys that are in the backup but not in the source. These files were deleted and must be removed from the backup
        deletedFiles = backupKeys - sourceKeys
        for file in deletedFiles:
            logger.info("Deleted file found: %s", file)

        filesToBackup = {
            "newFiles": newFiles,
            "modifiedFiles": set(),
            "deletedFiles": deletedFiles
        }

        # Go through the common files to check which might have been modified
        for file in commonFiles:
            if sourceDict[file]['hash'] != self.backupDict[file]['hash']:
                filesToBackup['modifiedFiles'].add(file)
                logger.info("Modified file found: %s", file)
        
        totalFileChange = self.__writeBackup(filesToBackup, sourceDict)

        #backupEndTime = time.time()
        logger.info("Backup completed in %s seconds. Total file change: %skb", time.time() - backupStartTime, str(totalFileChange[0] - totalFileChange[1]))

