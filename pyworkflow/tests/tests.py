
import sys
import os
import time
from traceback import format_exception
import unittest
from os.path import join, relpath
from itertools import izip

import pyworkflow as pw
from pyworkflow.project import Manager
from pyworkflow.object import Object, Float
from pyworkflow.protocol import MODE_RESTART, getProtocolFromDb


SMALL = 'small'
PULL_REQUEST = 'pull'
DAILY = 'daily'
WEEKLY = 'weekly'


# Procedure to check if a test class has an attribute called _labels and if so
# then it checks if the class test matches any of the labels in input label parameter.
def hasLabel(TestClass, labels):
    
    # Get _labels attributes in class if any.
    classLabels = getattr(TestClass, '_labels', None)

    # Check if no label in test class.    
    return classLabels is not None and any(l in classLabels for l in labels)


class DataSet:

    _datasetDict = {}  # store all created datasets

    def __init__(self, name, folder, files, url=None):
        """ 
        Params:
            
        #filesDict is dict with key, value pairs for each file
        """
        self._datasetDict[name] = self
        self.folder = folder
        self.path = join(pw.Config.SCIPION_TESTS, folder)
        self.filesDict = files
        self.url = url
        
    def getFile(self, key):
        if key in self.filesDict:
            return join(self.path, self.filesDict[key])
        return join(self.path, key)
    
    def getPath(self):
        return self.path
    
    @classmethod
    def getDataSet(cls, name):
        """
        This method is called every time the dataset want to be retrieved
        """
        assert name in cls._datasetDict, "Dataset: %s dataset doesn't exist." % name

        ds = cls._datasetDict[name]
        folder = ds.folder
        url = '' if ds.url is None else ' -u ' + ds.url

        if not pw.utils.envVarOn('SCIPION_TEST_NOSYNC'):
            command = ("%s %s testdata --download %s %s"
                       % (pw.PYTHON, pw.getScipionScript(), folder, url))
            print(">>>> %s" % command)
            os.system(command)
        return cls._datasetDict[name]


class BaseTest(unittest.TestCase):
    
    _labels = [WEEKLY]
     
    @classmethod
    def getOutputPath(cls, *filenames):
        """Return the path to the SCIPION_HOME/tests/output dir
        joined with filename"""
        return join(cls.outputPath, *filenames)   
    
    @classmethod
    def getRelPath(cls, basedir, filename):
        """Return the path relative to SCIPION_HOME/tests"""
        return relpath(filename, basedir)
    
    def launchProtocol(cls, prot, **kwargs):
        """ Launch a given protocol using cls.proj.
        Accepted **kwargs:
            wait: if True the function will return after the protocol runs.
                If not specified, then if waitForOutput is passed, wait is
                false.
            waitForOutputs: a list of expected outputs, ignored if wait=True
        """
        wait = kwargs.get('wait', None)
        waitForOutputs = kwargs.get('waitForOutput', [])

        if wait is None:
            wait = not waitForOutputs

        if getattr(prot, '_run', True):
            cls.proj.launchProtocol(prot, wait=wait)
            if not wait and waitForOutputs:
                while True:
                    time.sleep(10)
                    prot = cls.updateProtocol(prot)
                    if all(prot.hasAttribute(o) for o in waitForOutputs):
                        return prot
        
        if prot.isFailed():
            print("\n>>> ERROR running protocol %s" % prot.getRunName())
            print ("    FAILED with error: %s\n" % prot.getErrorMessage())
            logLines = prot.getLogsLastLines()
            for i in range(0, len(logLines)):
                print(logLines[i])
            raise Exception("ERROR launching protocol.")

        if not prot.isFinished() and not prot.useQueue():  # when queued is not finished yet
            print ("\n>>> ERROR running protocol %s" % prot.getRunName())
            logLines = prot.getLogsLastLines()
            for i in range(0, len(logLines)):
                print(logLines[i])
            raise Exception("ERROR: Protocol not finished")

        return prot
    
    @classmethod    
    def saveProtocol(cls, prot):
        """ Save protocol using cls.proj """
        cls.proj.saveProtocol(prot)

    @classmethod
    def _waitOutput(cls, prot, outputAttributeName):
        """ Wait until the output is being generated by the protocol. """

        def _loadProt():
            # Load the last version of the protocol from its own database
            prot2 = getProtocolFromDb(prot.getProject().path,
                                      prot.getDbPath(),
                                      prot.getObjId())
            # Close DB connections
            prot2.getProject().closeMapper()
            prot2.closeMappers()
            return prot2

        counter = 1
        prot2 = _loadProt()

        while not prot2.hasAttribute(outputAttributeName):
            time.sleep(5)
            prot2 = _loadProt()
            if counter > 1000:
                break
            counter += 1

        # Update the protocol instance to get latest changes
        cls.proj._updateProtocol(prot)
        
    @classmethod
    def newProtocol(cls, protocolClass, **kwargs):
        """ Create new protocols instances through the project
        and return a newly created protocol of the given class
        """
        # Try to continue from previous execution
        if pw.utils.envVarOn('SCIPION_TEST_CONTINUE'):
            candidates = cls.proj.mapper.selectByClass(protocolClass.__name__)
            if candidates:
                c = candidates[0]
                if c.isFinished():
                    setattr(c, '_run', False)
                else:
                    c.runMode.set(MODE_RESTART)
                return c
        return cls.proj.newProtocol(protocolClass, **kwargs)

    @classmethod
    def compareSets(cls, test, set1, set2):
        """ Iterate the elements of boths sets and check
        that all elements have equal attributes. """
        for item1, item2 in izip(set1, set2):
            areEqual = item1.equalAttributes(item2)
            if not areEqual:
                print("item 1 and item2 are different: ")
                item1.printAll()
                item2.printAll()
            test.assertTrue(areEqual)

    def assertSetSize(self, object, size=None, msg=None):
        """ Check if a pyworkflow Set is not None nor is empty"""
        self.assertIsNotNone(object, msg)

        if size is None:
            # Test is not empty
            self.assertNotEqual(object.getSize(), 0, msg)
        else:
            self.assertEqual(object.getSize(), size)

    def assertIsNotEmpty(self, object, msg=None):
        """ Check if the pworkflow object is not None nor is empty"""
        self.assertIsNotNone(object, msg)

        self.assertIsNotNone(object.get(), msg)


def setupTestOutput(cls):
    """ Create the output folder for a give Test class. """
    cls.outputPath = join(pw.Config.SCIPION_TESTS_OUTPUT, cls.__name__)
    pw.utils.cleanPath(cls.outputPath)
    pw.utils.makePath(cls.outputPath)
       

def setupTestProject(cls):
    """ Create and setup a Project for a give Test class. """
    projName = cls.__name__
    if os.environ.get('SCIPION_TEST_CONTINUE', None) == '1':
        proj = Manager().loadProject(projName)
    else:
        proj = Manager().createProject(projName) # Now it will be loaded if exists

    cls.outputPath = proj.path
    # Create project does not change the working directory anymore
    os.chdir(cls.outputPath)
    cls.projName = projName
    cls.proj = proj


class Complex(Object):
    """ Simple class used for tests here. """
    
    cGold = complex(1.0, 1.0)
    
    def __init__(self, imag=0., real=0., **args):
        Object.__init__(self, **args)
        self.imag = Float(imag)
        self.real = Float(real)
        # Create reference complex values
        
    def __str__(self):
        return '(%s, %s)' % (self.imag, self.real)
    
    def __eq__(self, other):
        return (self.imag == other.imag and 
                self.real == other.real)
            
    def hasValue(self):
        return True
    
    @classmethod
    def createComplex(cls):
        """Create a Complex object and set
        values with cls.cGold standard"""
        c = Complex() # Create Complex object and set values
        c.imag.set(cls.cGold.imag)
        c.real.set(cls.cGold.real)
        return c
       
    
class GTestResult(unittest.TestResult):
    """ Subclass TestResult to output tests results with colors
    (green for success and red for failure)
    and write a report on an .xml file. 
    """
    xml = None
    testFailed = 0
    numberTests = 0
    
    def __init__(self):
        unittest.TestResult.__init__(self)
        self.startTimeAll = time.time()
    
    def openXmlReport(self, classname, filename):
        pass
        
    def doReport(self):
        secs = time.time() - self.startTimeAll
        sys.stderr.write("\n%s run %d tests (%0.3f secs)\n" %
                         (pw.utils.greenStr("[==========]"),
                          self.numberTests, secs))
        if self.testFailed:
            sys.stderr.write("%s %d tests\n"
                             % (pw.utils.redStr("[  FAILED  ]"),
                                self.testFailed))
        sys.stdout.write("%s %d tests\n"
                         % (pw.utils.greenStr("[  PASSED  ]"),
                            self.numberTests - self.testFailed))

    def tic(self):
        self.startTime = time.time()
        
    def toc(self):
        return time.time() - self.startTime
        
    def startTest(self, test):
        self.tic()
        self.numberTests += 1         
    
    def getTestName(self, test):
        parts = str(test).split()
        name = parts[0]
        parts = parts[1].split('.')
        classname = parts[-1].replace(")", "")
        return "%s.%s" % (classname, name)
    
    def addSuccess(self, test):
        secs = self.toc()
        sys.stderr.write("%s %s (%0.3f secs)\n" %
                         (pw.utils.greenStr('[ RUN   OK ]'),
                          self.getTestName(test), secs))

    def reportError(self, test, err):
        sys.stderr.write("%s %s\n" % (pw.utils.redStr('[   FAILED ]'),
                                      self.getTestName(test)))
        sys.stderr.write("\n%s"
                         % pw.utils.redStr("".join(format_exception(*err))))
        self.testFailed += 1
                
    def addError(self, test, err):
        self.reportError(test, err)
        
    def addFailure(self, test, err):
        self.reportError(test, err)
