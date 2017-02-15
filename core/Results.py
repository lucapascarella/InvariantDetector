import csv
import os


class Results:
    fieldnames = ['ID', 'Project compilable', 'Generate testsuite', 'Testsuite compilable', 'Method', 'JUnit executable', 'DTrace file', 'Inv file', 'Inv txt', 'DTrace file prev', 'Inv file prev', 'Inv txt prev', '', 'Inv V1', 'Inv V2', 'Inv V1V2', 'Inv V1V2 M', 'Inv V1V2 X', 'Inv V2V1', 'Inv V2V1 M', 'Inv V2V1 X', 'Lines_added', 'Lines_deleted', 'Lines_tot', 'Author', 'File', 'Start Commit', 'Commit number', 'Commit', 'COMM2', 'COMM', 'TOT', 'ADEV',
                  'ADD', 'ADDN', 'DEL', 'DELN', 'BUG ID', 'BUG Created', 'BUG Closed', 'Fix Date', 'Fix Commit', 'BIC', 'Analyzed']


    def __init__(self, args, type):
        output = os.path.splitext(os.path.basename(args.output))[0]
        self.outFile = open(args.base + "/" + args.work + "/" + output + "_" + type + ".csv", 'a', newline='')
        self.outWriter = csv.DictWriter(self.outFile, fieldnames=self.fieldnames)
        self.outWriter.writeheader()
        self.resDict = {}

    def updateID(self, id):
        self.resDict['ID'] = id

    def updateAll(self, row):
        fieldnames = ['File', 'Start Commit', 'Commit number', 'Commit', 'COMM2', 'COMM', 'TOT', 'ADEV', 'ADD', 'ADDN', 'DEL', 'DELN', 'BUG ID', 'BUG Created', 'BUG Closed', 'Fix Date', 'Fix Commit', 'BIC', 'Analyzed']
        for i in fieldnames:
            self.resDict[i] = row[i]

    def updateCompilation(self, res):
        if res is True:
            self.resDict['Project compilable'] = "true"
        else:
            self.resDict['Project compilable'] = "false"

    def updateTestsuiteGeneration(self, res):
        self.resDict['Generate testsuite'] = res

    def updateTestsuiteCompilation(self, res):
        self.resDict['Testsuite compilable'] = res

    def updateTestsuiteExecution(self, res):
        self.resDict['JUnit executable'] = res

    def updateDaikonChicory(self, res):
        self.resDict['DTrace file'] = res

    def updateDaikonUncompress(self, res):
        self.resDict['Inv file'] = res

    def updateDaikonPrint(self, res):
        self.resDict['Inv txt'] = res

    def updateDaikonChicoryPrev(self, res):
        self.resDict['DTrace file prev'] = res

    def updateDaikonUncompressPrev(self, res):
        self.resDict['Inv file prev'] = res

    def updateDaikonPrintPrev(self, res):
        self.resDict['Inv txt prev'] = res

    def updateDaikonDiffV1(self, res):
        self.resDict['Inv V1'] = res

    def updateDaikonDiffV2(self, res):
        self.resDict['Inv V2'] = res

    def updateDaikonDiffV1V2(self, res):
        self.resDict['Inv V1V2'] = res

    def updateDaikonDiffV1V2_M(self, res):
        self.resDict['Inv V1V2 M'] = res

    def updateDaikonDiffV1V2_X(self, res):
        self.resDict['Inv V1V2 X'] = res

    def updateDaikonDiffV2V1(self, res):
        self.resDict['Inv V2V1'] = res

    def updateDaikonDiffV2V1_M(self, res):
        self.resDict['Inv V2V1 M'] = res

    def updateDaikonDiffV2V1_X(self, res):
        self.resDict['Inv V2V1 X'] = res

    def updateFileStat(self, added, deleted, lines, author):
        self.resDict['Lines_added'] = str(added)
        self.resDict['Lines_deleted'] = str(deleted)
        self.resDict['Lines_tot'] = str(lines)
        self.resDict['Author'] = author

    def cleanAll(self):
        for f in self.fieldnames:
            self.resDict[f] = "---"

    def flush(self):
        self.outWriter.writerow(self.resDict)
        self.outFile.flush()

    def close(self):
        self.outFile.close()
