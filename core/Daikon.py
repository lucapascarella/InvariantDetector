class Daikon:
    className = ""
    package = ""
    packagePath = ""
    srcPath = ""
    #buildLibPath = ""
    randoopDirName = "randoop"
    evosuiteDirName = "evosuite"
    compileDir = "/classes"
    daikonDir = "/daikon"

    methodsName = []

    # Do not change this definition
    # daikonRegexAllMethods = "\.[a-zA-Z]+\w*\("

    def __init__(self, projectName):
        self.workingDirectory = projectName

    def getRandoopRegex(self, className, method="[a-zA-Z]+\w*"):
        # self.daikonRegex = className + self.daikonRegexAllMethods
        if method == ".all":
            return className + "\..*\("
        else:
            return className + "\." + method + "\("


    def getEvosuiteRegex(self, className, testPrefix, method="[a-zA-Z]+\w*"):
        # self.daikonRegex = className + self.daikonRegexAllMethods
        if method == ".all":
            return className + testPrefix + "\..*\("
        else:
            return className + testPrefix + "\." + method + "\("