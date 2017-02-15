import os
import csv


class IndexFile:
    def __init__(self, basePath, tempDir, tempInputFile):
        self.basePath = basePath
        self.tempDir = tempDir
        self.tempInputFile = tempInputFile

    def getNextWork(self):
        index = self.checkIndexFile()

        with open(self.basePath + "/" + self.tempDir + "/" + self.tempInputFile, newline='') as inFile:
            inReader = csv.DictReader(inFile)
            next = False
            for row in inReader:
                id = row['ID']
                if index is None:
                    return id
                elif id == index:
                    next = True
                elif next is True:
                    return id

    def checkIndexFile(self):
        path = self.basePath + "/" + self.tempDir + "/index.txt"
        if not os.path.exists(path):
            out = open(path, "w")
            out.close()
            return None
        else:
            out = open(path, "r")
            lines = out.read().splitlines()
            out.close()
            if len(lines) > 0:
                return lines[len(lines) - 1]
            else:
                return None

    def getCommitAndFile(self, id):
        with open(self.basePath + "/" + self.tempDir + "/" + self.tempInputFile, newline='') as inFile:
            inReader = csv.DictReader(inFile)
            next = False
            for row in inReader:
                if id == row['ID']:
                    commit = row['Commit']
                    file = row['File']
                    return (commit, file)

    def getCommitNumber(self, id):
        with open(self.basePath + "/" + self.tempDir + "/" + self.tempInputFile, newline='') as inFile:
            inReader = csv.DictReader(inFile)
            next = False
            for row in inReader:
                if id == row['ID']:
                    return row['Commit number']

    def getRow(self, id):
        with open(self.basePath + "/" + self.tempDir + "/" + self.tempInputFile, newline='') as inFile:
            inReader = csv.DictReader(inFile)
            next = False
            for row in inReader:
                if id == row['ID']:
                    return row

    def updateIndex(self, id):
        with open(self.basePath + "/" + self.tempDir + "/index.txt", "a") as indexFile:
            indexFile.write(id + "\n")
            indexFile.close()
