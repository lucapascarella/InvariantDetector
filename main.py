import csv
import argparse
import fileinput
import glob
import os

import re

import shutil
from asyncore import read

from core.Args import Args
from core.IndexFile import IndexFile
from core.CommandWorker import CommandWorker
from core.Results import Results
from core.Daikon import Daikon
from core.Paths import Paths
from core.FileWorker import FileWorker
from core.ClassPathMaker import ClassPathMaker
from core.ToolsBean import ToolsBean

ranDict = {}
evoDict = {}

wicketClasspath = ":wicket-auth-roles/target/classes:wicket-cdi/target/classes:wicket-core/target/classes:wicket-datetime/target/classes:wicket-devutils/target/classes:wicket-examples/target/classes:wicket-experimental/target/classes:wicket-extensions/target/classes:wicket-guice/target/classes:wicket-ioc/target/classes:wicket-jmx/target/classes:wicket-objectssizeof-agent/target/classes:wicket-request/target/classes:wicket-spring/target/classes:wicket-util/target/classes:wicket-velocity/target/classes:/usr/share/java/slf4j-api.jar"
# Define the columns of the output (invariants) CSV file
fieldnames = ['ID', 'Start Commit', 'Commit number', 'Commit', 'File', 'Project compilable', 'Generate testsuite', 'Testsuite compilable', 'Method', 'JUnit', 'DTrace', 'Inv', 'Inv txt', 'Inv diff', 'Inv diff M', 'Inv diff X', 'JUnit prev', 'DTrace prev', 'Inv prev', 'Inv txt prev', 'Inv diff prev', 'Inv diff prev M', 'Inv diff prev X', 'Analyzed']
fieldnames_to_reset = ['Generate testsuite', 'Testsuite compilable', 'Method', 'JUnit', 'DTrace', 'Inv', 'Inv txt', 'Inv diff', 'Inv diff M', 'Inv diff X', 'JUnit prev', 'DTrace prev', 'Inv prev', 'Inv txt prev', 'Inv diff prev', 'Inv diff prev M', 'Inv diff prev X']


def createListOfCommits(args, tb):
    fieldnames = ['ID', 'File', 'Start Commit', 'Commit number', 'Commit', 'COMM2', 'COMM', 'TOT', 'ADEV', 'ADD', 'ADDN', 'DEL', 'DELN', 'BUG ID', 'BUG Created', 'BUG Closed', 'Fix Date', 'Fix Commit', 'BIC', 'Analyzed']
    outDict = {}
    elaborated = []

    # Instantiate CommandWorker
    c = CommandWorker(args.base + "/" + args.name, tb, args.command, args.response, args.error)

    # Preapre the intermedie file with the list of all commits
    tempPath = args.base + "/" + args.work + "/temp/"
    if not os.path.exists(tempPath):
        os.makedirs(tempPath)
    with open(tempPath + "commit_list_output.csv", 'w', newline='') as outFile:
        outWriter = csv.DictWriter(outFile, fieldnames=fieldnames)
        outWriter.writeheader()

        # Create an array of elaborated files
        try:
            with open(tempPath + "/index.txt", "r") as indexFile:
                lines = indexFile.read()
                for line in lines.split('\n'):
                    elaborated.append(line)
        except FileNotFoundError as e:
            pass

        # Read from input file all the commits
        with open(args.base + "/" + args.input, newline='') as inFile:
            inReader = csv.DictReader(inFile)
            idCount = 0
            for row in inReader:
                commit = row['Commit']
                file = row['File']
                date = row['Date']
                if "exclude" in args.exclude.lower() and 'test' in file.lower():
                    print("Excluded: " + file + " " + commit)
                else:
                    hashs = c.gitGetCommmitsHistory(commit, file)
                    outDict['File'] = file
                    outDict['Start Commit'] = commit
                    outDict['COMM2'] = str(len(hashs.split('\n')))
                    outDict['COMM'] = row['COMM']
                    outDict['TOT'] = row['TOT']
                    outDict['ADEV'] = row['ADEV']
                    outDict['ADDN'] = row['ADDN']
                    outDict['DEL'] = row['DEL']
                    outDict['DELN'] = row['DELN']
                    outDict['BUG ID'] = row['BUG ID']
                    outDict['BUG Created'] = row['BUG Created']
                    outDict['BUG Closed'] = row['BUG Close']  # Clode instead of Closed
                    outDict['Fix Date'] = row['Fix Date']
                    outDict['Fix Commit'] = row['Fix Commit']
                    outDict['BIC'] = row['BIC']
                    outDict['Analyzed'] = args.name
                    commitNumber = 0
                    for h in hashs.split('\n'):
                        outDict['Commit'] = h
                        outDict['Commit number'] = commitNumber
                        outDict['ID'] = str(idCount) + "_" + str(commitNumber) + "_" + args.name
                        wPath = args.base + "/" + args.work + "/" + outDict['ID']
                        # Remove all previous elements
                        remove = True
                        for line in elaborated:
                            if line == outDict['ID']:
                                remove = False
                        # removeDirRecursively(wPath)
                        if remove is True and os.path.exists(wPath):
                            for root, dirs, files in os.walk(wPath, topdown=False):
                                for name in files:
                                    os.remove(os.path.join(root, name))
                                for name in dirs:
                                    os.rmdir(os.path.join(root, name))
                            os.rmdir(wPath)
                        ##os.makedirs(wPath)
                        commitNumber += 1
                        outWriter.writerow(outDict)
                    idCount += 1


def removeDirRecursively(path):
    if os.path.exists(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(path)


def executeInvairants(args, tb):
    # Create Results handler
    resRandoop = Results(args, "randoop")
    resEvosuite = Results(args, "evosuite")

    # ClassPath extractor
    fw = FileWorker(args.base + "/" + args.name)
    d = Daikon(args.base + "/" + args.name)
    paths = Paths()

    findHistory = True
    prevCommit = prevnwID = ""
    prevRandoopUsable = prevEvosuiteUsable = False

    exit = False
    while exit is False:
        # Find next commit to work
        index = IndexFile(args.base + "/" + args.work, "temp", "commit_list_output.csv")
        nwID = index.getNextWork()
        if nwID == None:
            exit = True
        else:
            (commit, file) = index.getCommitAndFile(nwID)
            commitNumber = index.getCommitNumber(nwID)
            print("LOG. Start processing: " + nwID)

            # Find the previous nwID if the process was stopped
            if findHistory is True and int(commitNumber) > 0:
                prevnwID = nwID.split('_')[0] + "_" + str(int(nwID.split('_')[1]) - 1) + "_" + nwID.split('_')[2]
                prevCommit = index.getCommitNumber(prevnwID)
            findHistory = False

            resRandoop.cleanAll()
            resEvosuite.cleanAll()
            resRandoop.updateID(nwID)
            resEvosuite.updateID(nwID)
            resRandoop.updateAll(index.getRow(nwID))
            resEvosuite.updateAll(index.getRow(nwID))

            # Instantiate CommandWorker
            cmd = CommandWorker(args.base + "/" + args.name, tb, args.command, args.response, args.error)
            # Try to build project
            savepath = os.path.normpath(args.base) + os.sep + args.work + os.sep + nwID
            buildPath = compileProject(cmd, commit, args.compiler, savepath)

            # Get git statisticts
            (added, deleted, author) = cmd.gitShowStat(commit, file)
            numberOfLines = cmd.getNumberOfLinesInFile(commit, file)
            resRandoop.updateFileStat(added, deleted, numberOfLines, author)
            resEvosuite.updateFileStat(added, deleted, numberOfLines, author)

            # Check compile success
            if buildPath is False or buildPath == "":
                print("LOG. Project cannot compilable")
                resRandoop.updateCompilation(False)
                resEvosuite.updateCompilation(False)
                prevRandoopUsable = prevEvosuiteUsable = False
            else:
                print("LOG. Project compiled. Processing")
                resRandoop.updateCompilation(True)
                resEvosuite.updateCompilation(True)

                # Extract the ClassName, package and sources path from given file
                d.className = fw.findClassName(file)
                d.package = fw.findPackage(file)
                d.methodsName = fw.getMethodsName(file, False)
                d.packagePath = fw.getPackagePath(d.package)
                d.srcPath = fw.getSrcPath(file, d.packagePath)
                # Create classPath variable with: .jar libs and basic buildPath of the project
                paths.jarPath = args.jar
                paths.buildPath = buildPath
                # Output direcotires for Randoop, Evosuite and Daikon
                paths.randoopTestsuiteDir = args.base + "/" + args.work + "/" + nwID + "/randoop"
                paths.evosuiteTestsuiteDir = args.base + "/" + args.work + "/" + nwID + "/evosuite"
                paths.randoopTestsuiteDirPrev = args.base + "/" + args.work + "/" + prevnwID + "/randoop"
                paths.evosuiteTestsuiteDirPrev = args.base + "/" + args.work + "/" + prevnwID + "/evosuite"
                paths.randoopTestsuiteClassesDir = args.base + "/" + args.work + "/" + nwID + "/randoop"
                paths.evosuiteTestsuiteClassesDir = args.base + "/" + args.work + "/" + nwID + "/evosuite"
                paths.randoopDaikonDir = args.base + "/" + args.work + "/" + nwID + "/randoop/daikon"
                paths.evosuiteDaikonDir = args.base + "/" + args.work + "/" + nwID + "/evosuite/daikon"
                paths.randoopDaikonDirPrev = args.base + "/" + args.work + "/" + prevnwID + "/randoop/daikon"
                paths.evosuiteDaikonDirPrev = args.base + "/" + args.work + "/" + prevnwID + "/evosuite/daikon"
                # Name of the class under test
                testclass = d.package + "." + d.className
                # Full path of the class under test
                fileFullPath = os.path.normpath(os.path.normpath(args.base + os.sep + args.name) + os.sep + d.srcPath) + os.sep + os.path.normpath(d.packagePath + os.sep + d.className + ".java")

                # Execute randoop
                classpath = paths.jarPath + ":" + paths.buildPath
                if executeRandoop(cmd, classpath, paths.randoopTestsuiteDir, paths.randoopTestsuiteClassesDir, resRandoop, testclass, args.timeout) is True:
                    for method in d.methodsName:
                        randoopRegex = d.getRandoopRegex(d.className, method)
                        dtraceFile = d.className + "_" + method
                        executeDaikon(cmd, classpath, paths.randoopTestsuiteDir, paths.randoopDaikonDir, dtraceFile, resRandoop, randoopRegex, "RegressionTest")
                        if int(commitNumber) != 0 and prevRandoopUsable is True:
                            executeDaikonPrev(cmd, classpath, paths.randoopTestsuiteDirPrev, paths.randoopDaikonDir, dtraceFile + "_" + prevnwID, resRandoop, randoopRegex, "RegressionTest")
                            executeDaikonDiff(cmd, paths.randoopDaikonDir, paths.randoopDaikonDirPrev, paths.randoopDaikonDir, dtraceFile, prevnwID, resRandoop)
                            cmd.saveDiff(paths.randoopTestsuiteDir, d.className, fileFullPath, commit, prevCommit)
                    # Make a copy of the .java file
                    ##fileFullPath = os.path.normpath(os.path.normpath(args.base + os.sep + args.name) + os.sep + d.srcPath) + os.sep + os.path.normpath(d.packagePath + os.sep + d.className + ".java")
                    if os.path.exists(fileFullPath):
                        shutil.copy(fileFullPath, paths.randoopTestsuiteDir)
                    prevRandoopUsable = True
                else:
                    prevRandoopUsable = False

                # Execute evosuite
                classpath = paths.jarPath + ":" + paths.buildPath
                if executeEvosuite(cmd, classpath, paths.evosuiteTestsuiteDir, paths.evosuiteTestsuiteClassesDir, resEvosuite, testclass, args.timeout) is True:
                    for method in d.methodsName:
                        evosuiteRegex = d.getEvosuiteRegex(d.className, "_ESTest", method)
                        dtraceFile = d.className + "_" + method
                        executeDaikon(cmd, classpath, paths.evosuiteTestsuiteDir, paths.evosuiteDaikonDir, dtraceFile, resEvosuite, evosuiteRegex, testclass + "_ESTest")
                        if int(commitNumber) != 0 and prevEvosuiteUsable is True:
                            executeDaikonPrev(cmd, classpath, paths.evosuiteTestsuiteDirPrev, paths.evosuiteDaikonDir, dtraceFile + "_" + prevnwID, resEvosuite, evosuiteRegex, testclass + "_ESTest")
                            executeDaikonDiff(cmd, paths.evosuiteDaikonDir, paths.evosuiteDaikonDirPrev, paths.evosuiteDaikonDir, dtraceFile, prevnwID, resEvosuite)
                            cmd.saveDiff(paths.evosuiteTestsuiteDir, d.className, fileFullPath, commit, prevCommit)
                    # Make a copy of the .java file
                    ##fileFullPath = os.path.normpath(os.path.normpath(args.base + os.sep + args.name) + os.sep + d.srcPath) + os.sep + os.path.normpath(d.packagePath + os.sep + d.className + ".java")
                    if os.path.exists(fileFullPath):
                        shutil.copy(fileFullPath, paths.evosuiteTestsuiteDir)
                    prevEvosuiteUsable = True
                else:
                    prevEvosuiteUsable = False

                # Update the prev indexes
                prevCommit = commit
                prevFile = commit
                prevnwID = nwID

            # Write results into CSV file
            resRandoop.flush()
            resEvosuite.flush()
            index.updateIndex(nwID)
    resRandoop.close()
    resEvosuite.close()


def executeDaikonDiff(cmd, compiledTestDir, compiledTestDirPrev, daikonOutputDir, dtraceFile, prevnwID, res):
    dtraceFileV1 = os.path.normpath(compiledTestDirPrev) + os.sep + dtraceFile
    dtraceFileV2 = os.path.normpath(compiledTestDir) + os.sep + dtraceFile + "_" + prevnwID
    invV1 = cmd.getNumberOfInvariants(dtraceFileV1 + ".inv.txt")
    invV2 = cmd.getNumberOfInvariants(dtraceFileV2 + ".inv.txt")

    res.updateDaikonDiffV1(str(invV1))
    res.updateDaikonDiffV2(str(invV2))

    # Find invariants V1 - V2
    dtraceFileOut = os.path.normpath(daikonOutputDir) + os.sep + dtraceFile + "_V1-V2"
    savepath = compiledTestDir
    (res1, m1, x1) = cmd.runDaikonDiffInvariants(dtraceFileV1, dtraceFileV2, dtraceFileOut, savepath)
    if res1 is True:
        res.updateDaikonDiffV1V2("true")
        invV1V2_M = cmd.getNumberOfInvariants(dtraceFileOut + ".m.inv.txt")
        invV1V2_X = cmd.getNumberOfInvariants(dtraceFileOut + ".x.inv.txt")
        res.updateDaikonDiffV1V2_M(str(invV1V2_M))
        res.updateDaikonDiffV1V2_X(str(invV1V2_X))
    else:
        res.updateDaikonDiffV1V2("false")

    # Find invariants V2 - V1
    dtraceFileOut = os.path.normpath(daikonOutputDir) + os.sep + dtraceFile + "_V2-V1"
    savepath = compiledTestDir
    (res2, m2, x2) = cmd.runDaikonDiffInvariants(dtraceFileV2, dtraceFileV1, dtraceFileOut, savepath)
    if res2 is True:
        res.updateDaikonDiffV2V1("true")
        invV2V1_M = cmd.getNumberOfInvariants(dtraceFileOut + ".m.inv.txt")
        invV2V1_X = cmd.getNumberOfInvariants(dtraceFileOut + ".x.inv.txt")
        res.updateDaikonDiffV2V1_M(str(invV2V1_M))
        res.updateDaikonDiffV2V1_X(str(invV2V1_X))
    else:
        res.updateDaikonDiffV2V1("false")


def executeDaikon(cmd, classpath, compiledTestDir, daikonOutputDir, dtraceFile, res, regex, testsuiteName):
    savepath = daikonOutputDir
    if cmd.runDaikonDynComp(classpath + ":" + compiledTestDir, daikonOutputDir, dtraceFile, regex, testsuiteName, savepath) is False:
        res.updateDaikonChicory("false")
        print("LOG. Daikon Chicory error")
        return False
    else:
        if cmd.runDaikonChicory(classpath + ":" + compiledTestDir, daikonOutputDir, dtraceFile, regex, testsuiteName, savepath) is False:
            # TODO Add if statement here
            print("TODO")
        else:
            res.updateDaikonChicory("true")
            print("LOG. Daikon Chicory success")
            if cmd.runDaikonUncompress(daikonOutputDir, dtraceFile, savepath) is False:
                res.updateDaikonUncompress("false")
                print("LOG. Daikon Uncompress error")
                return False
            else:
                res.updateDaikonUncompress("true")
                print("LOG. Daikon Uncompress success")
                (rtn1, fempty1) = cmd.runDaikonPrintInvariants(daikonOutputDir, dtraceFile, savepath)
                if rtn1 is False:
                    res.updateDaikonPrint("false")
                    print("LOG. Daikon Print error")
                    return False
                else:
                    res.updateDaikonPrint("true")
                    print("LOG. Daikon Print success")
                    return True


def executeDaikonPrev(cmd, classpath, compiledTestDir, daikonOutputDir, dtraceFile, res, regex, testsuiteName):
    savepath = daikonOutputDir + "/prev"
    if cmd.runDaikonChicory(classpath + ":" + compiledTestDir, daikonOutputDir, dtraceFile, regex, testsuiteName, savepath) is False:
        res.updateDaikonChicoryPrev("false")
        print("LOG. Daikon Chicory prev error")
        return False
    else:
        res.updateDaikonChicoryPrev("true")
        print("LOG. Daikon Chicory prev success")
        if cmd.runDaikonUncompress(daikonOutputDir, dtraceFile, savepath) is False:
            res.updateDaikonUncompressPrev("false")
            print("LOG. Daikon Uncompress prev error")
            return False
        else:
            res.updateDaikonUncompressPrev("true")
            print("LOG. Daikon Uncompress prev success")
            (rtn1, fempty1) = cmd.runDaikonPrintInvariants(daikonOutputDir, dtraceFile, savepath)
            if rtn1 is False:
                res.updateDaikonPrintPrev("false")
                print("LOG. Daikon Print prev error")
                return False
            else:
                res.updateDaikonPrintPrev("true")
                print("LOG. Daikon Chicory prev success")
                return True


def executeRandoop(cmd, classpath, testsuiteOutputDir, testsuiteClassesDir, res, testclass, timeout):
    savepath = testsuiteOutputDir
    # Generate the testsuite with randoop
    regressionTestName = "RegressionTest"
    if cmd.runRandooop(classpath, testclass, testsuiteOutputDir, timeout, savepath) is False:
        res.updateTestsuiteGeneration("false")
        print("LOG. Randoop error")
        return False
    else:
        res.updateTestsuiteGeneration("true")
        print("LOG. Randoop success")
        if cmd.compileTestcases(classpath, testsuiteOutputDir, testsuiteClassesDir, regressionTestName, savepath) is False:

            res.updateTestsuiteCompilation("false")
            print("LOG. Randoop javac error")
            return False
        else:
            res.updateTestsuiteCompilation("true")
            print("LOG. Randoop javac success")
            if cmd.runJUnitTest(classpath + ":" + testsuiteClassesDir, regressionTestName, savepath) is False:
                res.updateTestsuiteExecution("false")
                print("LOG. Randoop JUnit error")
                return False
            else:
                res.updateTestsuiteExecution("true")
                print("LOG. Randoop JUnit success")
                return True


def executeEvosuite(cmd, classpath, testsuiteOutputDir, tastsuiteClassesDir, res, testclass, timeout):
    savepath = testsuiteOutputDir
    # Generate the testsuite with randoop
    regressionTestName = testclass + "_ESTest"
    if cmd.runEvosuite(classpath, testclass, testsuiteOutputDir, timeout, savepath) is False:
        res.updateTestsuiteGeneration("false")
        print("LOG. Evosuite error")
        return False
    else:
        res.updateTestsuiteGeneration("true")
        print("LOG. Evosuite success")
        if cmd.compileTestcases(classpath, testsuiteOutputDir, tastsuiteClassesDir, re.sub('\.', '/', regressionTestName), savepath) is False:
            res.updateTestsuiteCompilation("false")
            print("LOG. Evosuite javac error")
            return False
        else:
            res.updateTestsuiteCompilation("true")
            print("LOG. Evosuite javac success")
            if cmd.runJUnitTest(classpath + ":" + tastsuiteClassesDir, regressionTestName, savepath) is False:
                res.updateTestsuiteExecution("false")
                print("LOG. Evosuite JUnit error")
                return False
            else:
                res.updateTestsuiteExecution("true")
                print("LOG. Evosuite JUnit success")
                return True


def compileProject(cmd, commit, type, savePath):
    cmd.cleanWorkingDirectory()
    cmd.gitCheckout(commit)
    if type == "ant":
        cmd.antClean(savePath)
        buildPath = cmd.antCompile(savePath)
    else:
        cmd.mvnClean(savePath)
        buildPath = cmd.mvnCompile(savePath)
    return buildPath


def moveFiles(basepath, package, files):
    # Copy and delete the *.java files in the basic folder
    m = re.search('(.*)\.(.*)', package)
    if m:
        path = re.sub('\.', '/', m.group(1))  # Package
        regressionTestName = m.group(2)  # Class name
        for filename in glob.glob(os.path.join(basepath + "/" + path + "/", files)):
            shutil.copy(filename, basepath + "/")
        m = re.search('^(\w*)\.', package)
        if m:
            removeDirRecursively(basepath + "/" + m.group(1))


if __name__ == '__main__':
    print("*** IMDEA Main app started ***\n")
    a = Args()
    args = a.returnArgsList()

    tb = ToolsBean(args)
    createListOfCommits(args, tb)
    executeInvairants(args, tb)

    print("*** IMDEA Main app finished ***\n")
