import os
import subprocess
import re


class CommandWorker:
    workingDirectory = ""
    printCommand = False
    printResponse = False
    printError = False

    outputString = ""
    errorString = ""

    def __init__(self, projectName, toolsBean, command, response, error):
        self.workingDirectory = projectName
        self.java = toolsBean.javapath
        self.javac = toolsBean.javacpath
        self.junit = toolsBean.junitpath
        self.hamcrest = toolsBean.hamcrestpath
        self.randoop = toolsBean.randooppath
        self.evosuite = toolsBean.evosuitepath
        self.daikon = toolsBean.daikonpath

        if command.lower() == "true":
            self.printCommand = True
        if response.lower() == "true":
            self.printResponse = True
        if error.lower() == "true":
            self.printError = True

    def runCommand(self, command):
        if self.printCommand is True:
            print(command)

        cond = 10
        while cond > 0:
            try:
                p = subprocess.Popen(command, cwd=self.workingDirectory, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (output, err) = p.communicate()
                break
            except OSError as e:
                if e.errno == 11:
                    print("BlockingIOError: [Errno 11] Resource temporarily unavailable")
                    import time
                    time.sleep(0.5)
                else:
                    output = err = ""
                    cond -= 1
                    print(e)

        self.outputString = str(output.decode('utf-8'))
        self.errorString = str(err.decode('utf-8'))
        if self.printResponse is True:
            print(self.outputString)
        if self.printError is True and self.errorString is not "":
            print("Error stream: " + self.errorString)
        return (self.outputString, self.errorString)

    def cleanWorkingDirectory(self):
        self.runCommand('git clean -df')

    def antClean(self, savepath):
        self.runCommand('ant clean')

    def mvnClean(self, savepath):
        self.runCommand('mvn clean')

    def gitGetCommmitsHistory(self, hash, file):
        (history, err) = self.runCommand("git log --reverse --pretty=format:'%H' " + hash + " -- " + file)
        return history

    def gitCheckout(self, hash):
        (out, err) = self.runCommand("git checkout " + hash)

    def gitShowStat(self, hash, file):
        (out, err) = self.runCommand("git show --numstat --pretty=format:'%an' " + hash + " -- " + file)
        if out != "":
            lines = out.split("\n")
            if len(lines) > 0:
                author = lines[0]
                changes = lines[1].split("\t")
                added = changes[0]
                deleted = changes[1]
                return (added, deleted, author)
        return (-1, -1, "Not detected")

    def getNumberOfLinesInFile(self, hash, file):
        path = self.workingDirectory + os.sep + file
        if os.path.exists(path) is True:
            lines = open(path, "r").readlines()
            numberOfLines = len(lines)
            return numberOfLines
        return None

    def antCompile(self, savepath):
        cmd = "ant compile -DlastRevision=1"
        (out, err) = self.runCommand(cmd)
        self.saveCommand(savepath, "ant_compile", cmd, out, err)
        if "BUILD SUCCESSFUL" in out:
            # m = re.search('compile:\n.*\[javac].*source files to (.*)\n', out)
            m = re.search('\s\[javac\].*source files to (/.*)\n', out)
            if m:
                return m.group(1)
            else:
                m = re.search('\[copy\] Copying.*file.*to (/.*)\n', out)
                if m:
                    return m.group(1)
            return ""
        else:
            return False

    def mvnCompile(self, savepath):
        (out, err) = self.runCommand("mvn compile")
        return "BUILD SUCCESS" in out

    def runRandooop(self, buildpath, testclass, outputDir, timelimit, savepath):
        # Add randoop command to classpath
        classpath = self.randoop + ":" + buildpath
        # Execute randoop command
        cmd = self.java + " -ea -cp " + classpath + " randoop.main.Main gentests --testclass=" + testclass + " --junit-output-dir=" + outputDir + " --timelimit=" + str(timelimit)
        (out, err) = self.runCommand(cmd)
        self.saveCommand(savepath, "randoop", cmd, out, err)
        if "Writing JUnit test" in out:
            return True
        return False

    def runEvosuite(self, classPath, testclass, outputDir, timelimit, savepath):
        # -Dglobal_timeout=10
        cmd = self.java + " -jar " + self.evosuite + " -class " + testclass + " -projectCP " + classPath + " -Dtest_dir=" + outputDir + " -Dreport_dir=" + outputDir + " -Duse_separate_classloader=false -Dsearch_budget=" + str(timelimit)
        (out, err) = self.runCommand(cmd)
        self.saveCommand(savepath, "evosuite", cmd, out, err)
        if "Writing JUnit test case" in out:
            return True
        return False

    def mkdir(self, path):
        (out, err) = self.runCommand("mkdir " + path)
        return out

    def compileTestcases(self, classpath, sourceDir, outputDir, regressionTestName, savepath):
        classpath = classpath + ":" + self.junit + ":" + self.hamcrest + ":" + self.evosuite
        if sourceDir is not "":
            sourceDir = os.path.normpath(sourceDir) + os.sep
        cmd = self.javac + " -cp " + classpath + " " + sourceDir + regressionTestName + "*.java -d " + outputDir
        (out, err) = self.runCommand(cmd)
        self.saveCommand(savepath, "javac", cmd, out, err)
        if "file not found" in err:
            return False
        return True

    def runJUnitTest(self, classpath, regressionTestName, savepath):
        classpath = classpath + ":" + self.junit + ":" + self.hamcrest + ":" + self.evosuite
        cmd = self.java + " -ea -cp " + classpath + " org.junit.runner.JUnitCore " + regressionTestName
        (out, err) = self.runCommand(cmd)
        self.saveCommand(savepath, "junit", cmd, out, err)
        # if "OK (" in out:
        if "Tests run: " in out or "OK (" in out:
            return True
        return False

    def runDaikonDynComp(self, classpath, outputDir, dtraceFile, daikonRegex, regressionTestName, savepath):
        classpath = classpath + ":" + self.junit + ":" + self.hamcrest + ":" + self.daikon + ":" + self.evosuite
        cmd = self.java + " -ea -cp " + classpath + " daikon.DynComp --output-dir=" + outputDir + " --decl-file=" + dtraceFile + ".dtrace.gz --ppt-select-pattern='" + daikonRegex + "' org.junit.runner.JUnitCore " + regressionTestName
        (out, err) = self.runCommand(cmd)
        self.saveCommand(savepath, "chicory", cmd, out, err)
        if "Chicory warning: no records were printed" in out:
            return False
        return True

    def runDaikonChicory(self, classpath, outputDir, dtraceFile, daikonRegex, regressionTestName, savepath):
        classpath = classpath + ":" + self.junit + ":" + self.hamcrest + ":" + self.daikon + ":" + self.evosuite
        cmd = self.java + " -ea -cp " + classpath + " daikon.Chicory --output-dir=" + outputDir + " --dtrace-file=" + dtraceFile + ".dtrace.gz --ppt-select-pattern='" + daikonRegex + "' org.junit.runner.JUnitCore " + regressionTestName
        (out, err) = self.runCommand(cmd)
        self.saveCommand(savepath, "chicory", cmd, out, err)
        if "Chicory warning: no records were printed" in out:
            return False
        return True

    def runDaikonUncompress(self, invariantsDir, dtraceFile, savepath):
        classpath = self.daikon
        cmd = self.java + " -ea -cp " + classpath + " daikon.Daikon -o " + invariantsDir + "/" + dtraceFile + ".inv " + invariantsDir + "/" + dtraceFile + ".dtrace.gz"
        (out, err) = self.runCommand(cmd)
        self.saveCommand(savepath, "uncompress", cmd, out, err)
        if "FileNotFoundException" in out or "No program point declarations were found." in err or "No samples found for any of 10 program points" in err:
            return False
        return True

    def runDaikonPrintInvariants(self, invariantsDir, dtraceFile, savepath):
        classpath = self.daikon
        cmd = self.java + " -ea -cp " + classpath + " daikon.PrintInvariants " + invariantsDir + "/" + dtraceFile + ".inv --output=" + invariantsDir + "/" + dtraceFile + ".inv.txt"
        (out, err) = self.runCommand(cmd)
        self.saveCommand(savepath, "print", cmd, out, err)
        if "FileNotFoundException" not in out:
            path = invariantsDir + "/" + dtraceFile + ".inv.txt"
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return (True, "true")
            else:
                return (True, "false")
        return (False, "false")

    def runDaikonDiffInvariants(self, dtraceFile1, dtraceFile2, dtraceFileOut, savepath):
        dtraceFile1 = dtraceFile1 + ".inv"
        dtraceFile2 = dtraceFile2 + ".inv"
        m = x = "false"
        classpath = self.daikon
        if os.path.exists(dtraceFile1) is True and os.path.exists(dtraceFile2) is True:
            cmd = self.java + " -ea -cp " + classpath + " daikon.diff.Diff " + dtraceFile1 + " " + dtraceFile2 + " -m -o " + dtraceFileOut + ".m.inv"
            (out, err) = self.runCommand(cmd)
            self.saveCommand(savepath, "diffm", cmd, out, err)
            if err is not "":
                return (False, m, x)
            cmd = self.java + " -ea -cp " + classpath + " daikon.diff.Diff " + dtraceFile1 + " " + dtraceFile2 + " -x -o " + dtraceFileOut + ".x.inv"
            (out, err) = self.runCommand(cmd)
            self.saveCommand(savepath, "diffx", cmd, out, err)
            if err is not "":
                return (False, m, x)
        elif os.path.exists(dtraceFile1) is True and os.path.exists(dtraceFile2) is False:
            (out, err) = self.runCommand(self.java + " -ea -cp " + classpath + " daikon.diff.Diff " + dtraceFile1 + " -m -o " + dtraceFileOut + ".m.inv")
            if err is not "":
                return (False, m, x)
            (out, err) = self.runCommand(self.java + " -ea -cp " + classpath + " daikon.diff.Diff " + dtraceFile1 + " -x -o " + dtraceFileOut + ".x.inv")
            if err is not "":
                return (False, m, x)
        elif os.path.exists(dtraceFile1) is False and os.path.exists(dtraceFile2) is True:
            (out, err) = self.runCommand(self.java + " -ea -cp " + classpath + " daikon.diff.Diff " + dtraceFile2 + " -m -o " + dtraceFileOut + ".m.inv")
            if err is not "":
                return (False, m, x)
            (out, err) = self.runCommand(self.java + " -ea -cp " + classpath + " daikon.diff.Diff " + dtraceFile2 + " -x -o " + dtraceFileOut + ".x.inv")
            if err is not "":
                return (False, m, x)
        else:
            return (False, m, x)
        (outM, errM) = self.runCommand(self.java + " -ea -cp " + classpath + " daikon.PrintInvariants " + dtraceFileOut + ".m.inv --output=" + dtraceFileOut + ".m.inv.txt")
        (outX, errX) = self.runCommand(self.java + " -ea -cp " + classpath + " daikon.PrintInvariants " + dtraceFileOut + ".x.inv --output=" + dtraceFileOut + ".x.inv.txt")

        path = dtraceFileOut + ".m.inv.txt"
        if "FileNotFoundException" not in outM and os.path.exists(path) and os.path.getsize(path) > 0:
            m = "true"
        path = dtraceFileOut + ".x.inv.txt"
        if "FileNotFoundException" not in outX and os.path.exists(path) and os.path.getsize(path) > 0:
            x = "true"
        return (True, m, x)

    def getNumberOfInvariants(self, fullPath):
        if not os.path.exists(fullPath):
            return -1
        elif os.path.getsize(fullPath) == 0:
            return 0
        else:
            content = open(fullPath, 'r').read()
            m = re.findall('=*\n.*:::(CLASS|OBJECT|ENTER|EXIT)', content)
            if m:
                return len(m)
            else:
                return 0

    def saveCommand(self, dest, file, cmd, out, err):
        dest = os.path.normpath(dest) + os.sep + "cmd"
        if not os.path.exists(dest):
            os.makedirs(dest)
        dest += os.sep + file
        f = open(dest + ".cmd.txt", 'a')
        f.write(cmd)
        f.close()
        f = open(dest + ".out.txt", 'a')
        f.write(out)
        f.close()
        f = open(dest + ".err.txt", 'a')
        f.write(err)
        f.close()

    def saveDiff(self, savepath, classname, file, commit, prevCommit):
        savepath = os.path.normpath(savepath) + os.sep + classname + ".diff"
        (out, err) = self.runCommand("git diff " + commit + " " + prevCommit + " -- " + file + " > " + savepath)
