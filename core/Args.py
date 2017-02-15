import argparse
import os


class Args:

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument("-n", "--name", help="Project name", default="zookeeper")
        parser.add_argument("-b", "--base", help="Absolute base path", default="/home/luca/data/IMDEA/projects")

        #parser.add_argument("-t", "--tools", help="Tools classpath", default="/home/luca/data/IMDEA/tools/*:/home/luca/data/IMDEA/tools/hamcrest-core.jar:/home/luca/data/IMDEA/tools/junit.jar:/home/luca/data/IMDEA/tools/randoop-all.jar:/home/luca/data/IMDEA/tools/daikon/daikon.jar:/home/luca/data/IMDEA/tools/evosuite.jar")
        parser.add_argument("-z", "--toolspath", help="Basic tools classpath", default="/home/luca/data/IMDEA/tools/")
        parser.add_argument("-u", "--junit", help="JUnit classpath", default="junit.jar")
        parser.add_argument("-m", "--hamcrest", help="JUnit classpath", default="hamcrest-core.jar")
        parser.add_argument("-ra", "--randoop", help="Randoop classpath", default="randoop-all.jar")
        parser.add_argument("-s", "--evosuite", help="Evosuite classpath", default="evosuite.jar")
        parser.add_argument("-d", "--daikon", help="Daikon classpath", default="daikon/daikon.jar")

        parser.add_argument("-a", "--jar", help="Classpath to JAR file lib (Used by compiler)", default="/home/luca/data/IMDEA/tools/log4j-1.2.17.jar")

        parser.add_argument("-x", "--compiler", help="Maven or Ant compiler task", default="ant")
        parser.add_argument("-w", "--work", help="Working directory", default="inv")
        parser.add_argument("-i", "--input", help="CSV input file", default="test_zookeeper.csv")
        parser.add_argument("-o", "--output", help="CSV output file", default="output_zookeeper.csv")

        parser.add_argument("-l", "--timeout", help="Rundoop timelimit", default="15")

        parser.add_argument("-j", "--java", help="java tool base path", default="java")
        parser.add_argument("-k", "--javac", help="javac tool base path", default="javac")

        parser.add_argument("-g", "--exclude", help="Include or exclude tests files", default="exclude")

        parser.add_argument("-c", "--command", help="Print command", default="true")
        parser.add_argument("-r", "--response", help="Print response", default="false")
        parser.add_argument("-e", "--error", help="Print error", default="true")

        # parser.add_argument("-c", "--build", help="Build path in the project", default="build/classes/")
        # parser.add_argument("-l", "--lib", help="Build libraries path in the project", default="build/lib/*")
        # parser.add_argument("-e", "--classpath", help="Classpath", default=":.:/home/luca/data/IMDEA/tools/*:/home/luca/data/IMDEA/tools/hamcrest-core.jar:/home/luca/data/IMDEA/tools/junit.jar:/home/luca/data/IMDEA/tools/randoop-all.jar:/home/luca/data/IMDEA/tools/daikon/daikon.jar:/home/luca/data/IMDEA/tools/evosuite.jar")
        #parser.add_argument("-r", "--regression", help="Regression test output name", default="RegressionTest")
        #parser.add_argument("-i", "--tools", help="jar tools base path", default="/home/luca/data/IMDEA/tools/")

        self.args = parser.parse_args()

        inputFile = self.args.base + "/" + self.args.input
        if not os.path.exists(inputFile):
            print("Input file not found: " + inputFile)
            exit(1)

        workdir = self.args.base + "/" + self.args.work
        if not os.path.exists(workdir):
            os.makedirs(workdir)


    def returnArgsList(self):
        return self.args
