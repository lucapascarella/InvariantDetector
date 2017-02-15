import os

class ToolsBean:

    def __init__(self, args):
        self.toolpath = args.toolspath
        self.java = args.java
        self.javac = args.javac
        self.junit = args.junit
        self.hamcrest = args.hamcrest
        self.randoop = args.randoop
        self.evosuite = args.evosuite
        self.daikon = args.daikon

        # Create the absolute paths to every tools
        self.javapath = os.path.normpath(self.java) # Aggiunre controllo esistenza
        self.javacpath = os.path.normpath(self.javac) # Aggiungere controllo esistenza
        self.junitpath = os.path.normpath(self.toolpath) + os.sep + self.junit
        self.hamcrestpath = os.path.normpath(self.toolpath) + os.sep + self.hamcrest
        self.randooppath = os.path.normpath(self.toolpath) + os.sep + self.randoop
        self.evosuitepath = os.path.normpath(self.toolpath) + os.sep + self.evosuite
        self.daikonpath = os.path.normpath(self.toolpath) + os.sep + self.daikon


