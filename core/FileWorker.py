import re
import os


class FileWorker:
    workingDirectory = ""
    printCommands = True

    def __init__(self, projectName):
        self.workingDirectory = projectName

    def findPackage(self, file):
        if not os.path.exists(self.workingDirectory + '/' + file):
            return ""
        else:
            f = open(self.workingDirectory + '/' + file, 'r')
            string = f.read()
            m = re.search('package ([a-zA-Z_]+[a-zA-Z0-9_.]*)', string)
            f.close()
            if m:
                sub = m.group(1)
                return sub
            return ""

    def findClassName(self, file):
        return os.path.splitext(os.path.basename(file))[0]

    def getPackagePath(self, package):
        return re.sub('\.', '/', package)

    def getSrcPath(self, file, package):
        return file[:file.find(package)]

    def getMethodsName(self, file, populate):
        methods = []
        methods.append(".all")
        if populate is True:
            if os.path.exists(self.workingDirectory + '/' + file):
                f = open(self.workingDirectory + '/' + file, 'r')
                string = f.read()
                matchs = re.findall('(public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *(\{?|[^;])', string)
                f.close()
                if matchs:
                    for m in matchs:
                        method = m[1]
                        # print(method)
                        methods.append(method)
        return methods
