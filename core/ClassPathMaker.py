import os

class ClassPathMaker:

    classpath = ""

    def __init__(self, path):
        self.classpath = path

    def addPath(self, path):
        if os.path.exists(path):
            self.classpath = self.classpath + ":" + path

    def addMultiplePath(self, path):
        #if os.path.exists(path):
        self.classpath = self.classpath + ":" + path

    def returnClassPath(self):
        return self.classpath