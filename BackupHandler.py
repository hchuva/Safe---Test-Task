import time
import os
import logging
from configparser import ConfigParser
from HashGenerators import MD5Generator, SHA256Generator, CRC32Generator
from FileHandler import FileSystemHandler

logger = logging.getLogger('backup')

#TODO: Remove config fil code
#TODO: Use the FileHandler Cleanup function to remove empty directories
#TODO: Use the FileHandler Walk function to get all files in a directory

class BackupHandler:

    hashingAlgorithms = {
        "md5": MD5Generator,
        "sha256": SHA256Generator,
        "crc32": CRC32Generator
    }

    backupStrategies = {
        "fileSystem": FileSystemHandler,
    }

    def __init__(self, backupInterval: int, backupPath: str = "", sourcePath: str = "", hashAlgorithm: str = "md5", backupStrategy: str = "fileSystem"):
        logger.info("Initializing Backup Handler")
        #self.readConfig(config)

        self.backupInterval = backupInterval
        self.backupPath = backupPath
        self.sourcePath = sourcePath
        self.hashAlgorithm = self.__getHashingAlgorithm(hashAlgorithm)
        self.backupStrategy = self.__getBackupStrategy(backupStrategy)

        # Create the dictionary that will store and track the backup data
        self.__readBackup()

        # Create the tim tracking variable
        self.lastBackup = time.time()
        
    def readConfig(self, config: ConfigParser):
        self.backupPath = config["DEFAULT"]["backupPath"]
        self.sourcePath = config["DEFAULT"]["sourcePath"]
        self.hashAlgorithm = self.__getHashingAlgorithm(config["DEFAULT"]["hashAlgorithm"])
        self.backupStrategy = self.__getBackupStrategy(config["DEFAULT"]["backupStrategy"])


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
        while True:
            if time.time() - self.lastBackup >= self.backupInterval:
                logger.info("Backup Interval reached. Running backup")
                self.lastBackup = time.time()
                self.__backupSource()

    def __readBackup(self):
        # Lets first get all the files in the backup directory
        fileList = self.__walkDirectory(self.backupPath)

        # Now lets open each file and hash it
        self.backupDict = self.__hashFileList(fileList, self.backupPath)

    def __hashFileList(self, fileList: dict, path: str):
        
        for file in fileList:
            #with open(path + "/" + file, "r") as f:
            #    data = f.read()
            #    hashedData = self.hashAlgorithm.hashFile(data)
            #    hashedFiles[file] = hashedData
            fileData, _ = self.backupStrategy.ReadFile(path + "/" + file)
            hashedData = self.hashAlgorithm.hashFile(fileData)
            fileList[file]["hash"] = hashedData

        return fileList

    def __walkDirectory(self, path: str) -> dir:
        fileList = {}
        for dirpath, _, filenames in os.walk(path):
            for file_name in filenames:
                #fileList.append(dirpath.replace(path, "") + "/" + file_name)
                fileList[dirpath.replace(path, "") + "/" + file_name] = {
                    "path": dirpath.replace(path, ""),
                    "file": file_name
                }
        
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
        for dirpath, _, _ in os.walk(self.backupPath):
            if len(os.listdir(dirpath)) == 0:
                logger.info("Deleting empty directory: %s", dirpath)
                self.backupStrategy.DeleteDirectory(dirpath)

        return totalFileChange
    
    def __backupSource(self):

        backupStartTime = time.time()

        sourceDict = {}

        # Lets first get all the files in the source directory
        fileList = self.__walkDirectory(self.sourcePath)

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

