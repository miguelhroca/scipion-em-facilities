'''
Created on May 20, 2013

@author: laura
'''

from glob import iglob
from itertools import izip
import sqlite3
import numpy as np


from pyworkflow.tests import *
import pyworkflow.utils as pwutils
from pyworkflow.utils import Timer

import pwem.convert as emconv
import pwem.objects as emobj
import pwem.metadata as md

# try:
#     from xmipp3.convert import *
# except:
#     Domain._pluginNotFound('xmipp', doRaise=True)

#xmippConvert = Domain.importFromPlugin('xmipp3.convert', doRaise=True)

# set to true if you want to check how fast is the access to
# the database
SPEEDTEST = True


def getIndex(fileName):
    """ Returns list of indexes for the table 'objects'
    in the database fileName"""
    conn = sqlite3.connect(fileName)
    cur = conn.cursor()
    cur.execute("PRAGMA index_list(objects);")
    rows = cur.fetchall()
    conn.close()
    return rows  # list with index names


def dropIndex(fileName, indexName):
    """ Drop index called indexName for table objects
    in database fileName"""
    conn = sqlite3.connect(fileName)
    cur = conn.cursor()
    cur.execute("DROP INDEX %s" % indexName)
    conn.close()


def createDummyProtocol(projName):
    """create a dummy protocol, returns protocol object"""
    proj = Manager().createProject(projName)
    os.chdir(proj.path)

    from pwem.protocol import EMProtocol

    prot = proj.newProtocol(EMProtocol)
    prot.setObjLabel('dummy protocol')
    try:
        proj.launchProtocol(prot)
    except Exception as e:
        print (str(e))
    return prot
 

class TestFSC(unittest.TestCase):
    
    _labels = [SMALL, WEEKLY]
        
    def testIO(self):
        """Test basic FSC object"""
        xList=[0.00,0.05,0.10,0.15,0.2]
        yList=[1.00,0.95,0.90,0.85,0.2]
        fsc = emobj.FSC()
        fsc.setData(xList,yList)
        #fsc.printAll()
        x,y = fsc.getData()
        self.assertEqual(xList,x)
        self.assertEqual(yList,y)

    def testMd(self):
        """test create FSC from metdata"""
        import xmippLib
        xList=[0.00,0.05,0.10,0.15,0.2]
        yList=[1.00,0.95,0.90,0.85,0.2]
        md1 =xmippLib.MetaData()
        for freq,fscValue in izip(xList, yList):
            id = md1.addObject()
            md1.setValue(xmippLib.MDL_RESOLUTION_FREQ, freq, id)
            md1.setValue(xmippLib.MDL_RESOLUTION_FRC, fscValue, id)
        fsc = emobj.FSC()
        fsc.loadFromMd(md1,xmippLib.MDL_RESOLUTION_FREQ,
                       xmippLib.MDL_RESOLUTION_FRC)
        x,y = fsc.getData()
        self.assertEqual(xList,x)
        self.assertEqual(yList,y)


class TestImage(unittest.TestCase):

    _labels = [SMALL, WEEKLY]

    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)
        cls.dataset = DataSet.getDataSet('xmipp_tutorial')
        cls.mic1 = cls.dataset.getFile( 'mic1')

    def testLocation(self):
        fn = self.mic1
        mic = emobj.Micrograph()
        mic.setFileName(fn)

        # Check that setFileName-getFileName is working properly
        self.assertEqual(fn, mic.getFileName())

        # Check the location is accepted from constructor
        mic2 = emobj.Micrograph(fn)
        self.assertEqual(fn, mic2.getFileName())

        volStk = '/data/current/volumes/all_volumes.stk'
        vol1 = emobj.Volume((1, volStk))
        self.assertEqual(1, vol1.getIndex())
        self.assertEqual(volStk, vol1.getFileName())

        self.assertEqual('all_volumes.stk', vol1.getBaseName())

    def testOrigin(self):
        fn = self.mic1
        mic = emobj.Micrograph()
        mic.setFileName(fn)
        mic.setSamplingRate(1.)

        referenceT = emobj.Transform()
        referenceT.setShifts(-4608.,-4720.,1)
        mreferenceT = referenceT.getMatrix()

        t = mic.getOrigin(True)
        mt = t.getMatrix()
        for i in range(4):
            for j in range(4):
                self.assertAlmostEquals(mt[i][j],mreferenceT[i][j],delta=0.5)


class TestImageHandler(unittest.TestCase):

    _labels = [SMALL, WEEKLY]
    
    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)
        cls.dataset = DataSet.getDataSet('xmipp_tutorial')
        cls.dsFormat = DataSet.getDataSet('movies')

    def testExistLocation(self):
        volFn = self.dataset.getFile('volumes/volume_1_iter_002.mrc')

        ih = emconv.ImageHandler()
        # Test the volume filename exists
        self.assertTrue(ih.existsLocation(volFn))
        # Test missing filename
        self.assertFalse(ih.existsLocation(volFn.replace('.mrc', '_fake.mrc')))
        # Test the :mrc is append when used as volume
        newFn = ih.getVolFileName(volFn)
        self.assertEqual(newFn, volFn + ":mrc")
        # Test that the new filename still exists even with the :mrc suffix
        self.assertTrue(ih.existsLocation(newFn))

    def test_convertMicrographs(self):
        """ Convert micrograhs to different formats.
         EMAN2 required for .img
        """
        micFn = self.dataset.getFile('micrographs/BPV_1386.mrc')
        outSuffix = pwutils.replaceBaseExt(micFn, 'img')
        ih = emconv.ImageHandler()

        outFn = join('/tmp', outSuffix)
        print("Converting: \n%s -> %s" % (micFn, outFn))

        ih.convert(micFn, outFn)

        self.assertTrue(os.path.exists(outFn))
        self.assertTrue(pwutils.getFileSize(outFn) > 0)

        pwutils.cleanPath(outFn)
        pwutils.cleanPath(outFn.replace('.img', '.hed'))

    def test_readDM4(self):
        """ Check we can read dm4 files (using EMAN)
        """
        micFn = self.dsFormat.getFile('SuperRef_c3-adp-se-xyz-0228_001.dm4')

        ih = emconv.ImageHandler()
        # Check that we can read the dimensions of the dm4 file:
        EXPECTED_SIZE = (7676, 7420, 1, 1)
        self.assertEqual(ih.getDimensions(micFn), EXPECTED_SIZE)

        # We could even convert to an mrc file:
        outSuffix = pwutils.replaceBaseExt(micFn, 'mrc')

        outFn = join('/tmp', outSuffix)
        print("Converting: \n%s -> %s" % (micFn, outFn))

        ih.convert(micFn, outFn)

        self.assertTrue(os.path.exists(outFn))
        self.assertTrue(pwutils.getFileSize(outFn) > 0)
        # Check dimensions are still the same:
        self.assertEqual(ih.getDimensions(outFn), EXPECTED_SIZE)

        # Clean up tmp files
        pwutils.cleanPath(outFn)

    def test_readCompressedTIF(self):
        """ Check we can read tif files
        """
        micFn = self.dsFormat.getFile('c3-adp-se-xyz-0228_200.tif')

        ih = emconv.ImageHandler()
        # Check that we can read the dimensions of the dm4 file:
        EXPECTED_SIZE = (7676, 7420, 1, 38)
        self.assertEqual(ih.getDimensions(micFn), EXPECTED_SIZE)

        # We could even convert to an mrc file:
        outSuffix = pwutils.replaceBaseExt(micFn, 'mrc')

        outFn = join('/tmp', outSuffix)
        print("Converting: \n%s -> %s" % ((1, micFn), outFn))

        ih.convert((1, micFn), outFn)

        self.assertTrue(os.path.exists(outFn))
        self.assertTrue(pwutils.getFileSize(outFn) > 0)
        self.assertEqual(ih.getDimensions(outFn), (7676, 7420, 1, 1))

        # Clean up tmp files
        pwutils.cleanPath(outFn)
    
    def test_convertMovie(self):
        """Check movie conversion"""
        movFn = self.dsFormat.getFile('qbeta/qbeta.mrc') + ":mrcs"
        
        ih = emconv.ImageHandler()
        # Check that we can read the dimensions of the dm4 file:
        EXPECTED_SIZE = (4096, 4096, 1, 7)
        EXPECTED_DT = emconv.ImageHandler.DT_USHORT

        self.assertEqual(ih.getDimensions(movFn), EXPECTED_SIZE)
        self.assertEqual(ih.getDataType(movFn), EXPECTED_DT)
        
        outFn = join('/tmp/qbeta_converted.mrcs')

        ih.convertStack(movFn, outFn, 2, 6)
        
        self.assertTrue(os.path.exists(outFn))
        self.assertTrue(pwutils.getFileSize(outFn) > 0)
        self.assertEqual(ih.getDimensions(outFn), (4096, 4096, 1, 5))
        self.assertEqual(ih.getDataType(outFn), EXPECTED_DT)

        if pwutils.envVarOn('SCIPION_DEBUG_NOCLEAN'):
            print("Not cleaning output movie: ", outFn)
        else:
            pwutils.cleanPath(outFn)

    def test_truncateMask(self):
        ih = emconv.ImageHandler()

        maskFn = self.dataset.getFile('masks/mask.vol')
        outFn = join('/tmp', 'mask.vol')

        ih.truncateMask(maskFn, outFn, newDim=128)
        EXPECTED_SIZE = (128, 128, 128, 1)

        self.assertTrue(os.path.exists(outFn))
        self.assertTrue(pwutils.getFileSize(outFn) > 0)
        self.assertEqual(ih.getDimensions(outFn), EXPECTED_SIZE)

        pwutils.cleanPath(outFn)

    def test_createEmptyImage(self):
        outFn = join('/tmp', 'empty.mrc')
        SIZE = (128, 128, 1, 1)
        ih = emconv.ImageHandler()
        DT = ih.DT_FLOAT
        ih.createEmptyImage(outFn, SIZE[0], SIZE[1], dataType=DT)

        self.assertTrue(pwutils.getFileSize(outFn) > 0)
        self.assertEqual(ih.getDimensions(outFn), SIZE)
        self.assertEqual(ih.getDataType(outFn), DT)


class TestSetOfMicrographs(BaseTest):

    _labels = [SMALL, WEEKLY]

    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)
        cls.dataset = DataSet.getDataSet('xmipp_tutorial')  
        cls.dbGold = cls.dataset.getFile('micsGoldSqlite')
        cls.micsPattern = cls.dataset.getFile('allMics')
        cls.dbFn = cls.getOutputPath('micrographs.sqlite')
        cls.acquisition = emobj.Acquisition(magnification=60000, voltage=300,
                                            sphericalAberration=2,
                                            amplitudeContrast=0.1)
        
        #cls.mics = glob(cls.micsPattern)
        cls.mics = []
        for mic in iglob(cls.micsPattern):
            cls.mics.append(cls.getRelPath(cls.dataset.getPath(), mic))
        
        if len(cls.mics) == 0:
            raise Exception('There are not micrographs matching pattern')
        cls.mics.sort()                 
    
    def checkSet(self, micSet):
        idCount = 1
    
        for mic1, fn in izip(micSet, self.mics):  
            #traceback.print_stack(file=sys.stdout)
            micFn = mic1.getFileName()
            self.assertEqual(fn, micFn, 
                             "micrograph NAME in the set is wrong, \n   expected: '%s'\n        got: '%s'" 
                             % (fn, micFn))
            self.assertEqual(idCount, mic1.getObjId(), 
                             "micrograph ID in the set is wrong, \n   expected: '%s'\n        got: '%s'" 
                             % (idCount, mic1.getObjId()))
            mic2 = micSet[idCount] # Test getitem
            self.assertEqual(mic1.getObjId(), mic2.getObjId(), "micrograph got from ID is wrong")
            idCount += 1           
             
    def testCreate(self):
        cwd = os.getcwd()
        # Change to test path
        os.chdir(self.dataset.getPath())
        """ Create a SetOfMicrographs from a list of micrographs """
        micSet = emobj.SetOfMicrographs(filename=self.dbFn)
        
        micSet.setAcquisition(self.acquisition)
        micSet.setSamplingRate(1.2)
        for fn in self.mics:
            mic = emobj.Micrograph()
            mic.setFileName(fn)
            micSet.append(mic)
        micSet.write()    
        
        self.checkSet(micSet)
        
        # Check copy info also copies the samplingRate
        micSet2 = emobj.SetOfMicrographs(filename=':memory:')
        micSet2.copyInfo(micSet)
        self.assertAlmostEqual(micSet.getSamplingRate(), micSet2.getSamplingRate())
         
        os.chdir(cwd)
        
    def testRead(self):
        """ Read micrographs from a an sqlite file.
        It should contains Acquisition info. """
        micFn = self.dataset.getFile('micsGoldSqlite2')
        print(">>> Reading gold micrographs from: ", micFn)
        
        micSet = emobj.SetOfMicrographs(filename=micFn)
        self.assertEqual(2, micSet.getSize())
        acquisition=emobj.Acquisition()
        acquisition.setMagnification(10000.)
        acquisition.setVoltage(200.)
        acquisition.setSphericalAberration(2.26)
        acquisition.setAmplitudeContrast(0.1)
        
        mic2=emobj.Micrograph()
        mic2.setSamplingRate(2.8)
        mic2.setAcquisition(acquisition)

        fileNames=['/home/roberto/Scipion/Test/Test2/down2_12585',
                   '/home/roberto/Scipion/Test/Test2/down2_12610']
        counter=0
        for mic in micSet:
            mic2.setFileName(fileNames[counter])
            self.assertTrue(mic.equalAttributes( mic2))
            counter += 1

    def test_mapper(self):
        """ test that indexes are created when a
        setOfParticles is created """
        MICNUMBER = 10
        indexesNames = ['_index']
        prot = createDummyProtocol("dummy_protocol")

        # create set of micrographs
        micSet = prot._createSetOfMicrographs()
        mic = emobj.Micrograph()
        for i in range(MICNUMBER+ 1):
            mic.setLocation(i, "stack.stk")
            micSet.append(mic)
            mic.cleanObjId()
            micSet.write()

        # check defined indexes
        setOfMicrographsFileName = prot._getPath("micrographs.sqlite")
        # print os.path.abspath(setOfPArticleFileName)
        indexes = sorted([index[1] for index in
                          getIndex(setOfMicrographsFileName)])
        for index, indexName in zip(indexes, indexesNames):
            self.assertEqual(index, 'index_' + indexName )


class TestSetOfParticles(BaseTest):
    """ Check if the information of the images is copied to another image when
    a new SetOfParticles is created"""

    _labels = [SMALL, WEEKLY]

    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)
        cls.dataset = DataSet.getDataSet('xmipp_tutorial')
        
    def test_orderBy(self):
        #create setofProjections sorted
        imgSet1 = emobj.SetOfParticles(filename=':memory:',prefix='set1')
        imgSet2 = emobj.SetOfParticles(filename=':memory:',prefix='set2')
        imgSet1.setSamplingRate(1.5)
        imgSet2.setSamplingRate(1.5)
        img = emobj.Particle()

        for i in range(1, 10):
            img.setLocation(i, 'mystack.stk')
            img.setMicId(10-i)
            img.setClassId(i%5)
            imgSet1.append(img)
            img.setMicId(i)
            imgSet2.append(img)
            img.cleanObjId()
        #orderby
        for item1, item2 in izip(imgSet1.iterItems(orderBy='_micId',
                                                   direction='ASC'),
                                 imgSet2.iterItems(orderBy='_micId',
                                                   direction='ASC')):
            self.assertEquals(item1.getMicId(), item2.getMicId())

    def test_readStack(self):
        """ Read an stack of 29 particles from .hdf file.
        Particles should be of 500x500 pixels.
        """
        size = 29
        xdim = 500        
        inStack = self.dataset.getFile( 'particles1')
        outFn = self.getOutputPath('particles.sqlite')
        
        imgSet = emobj.SetOfParticles(filename=outFn)
        imgSet.setSamplingRate(1.0)
        imgSet.readStack(inStack) # This should add 29 new items to the set
        
        self.assertEquals(size, imgSet.getSize()) # Check same size
        self.assertEquals(xdim, imgSet.getDim()[0]) # Check same dimensions
        
        print("writing particles to: ", outFn)
        imgSet.write()
        
        imgSet2 = emobj.SetOfParticles(filename=':memory:')
        imgSet2.copyInfo(imgSet)
        self.assertAlmostEqual(imgSet.getSamplingRate(), imgSet2.getSamplingRate())
        
    def test_hugeSet(self):
        """ Create a set of a big number of particles to measure
        creation time with sqlite operations. 
        """
        # Allow what huge means to be defined with environment var
        n = int(os.environ.get('SCIPION_TEST_HUGE', 10000))
        print(">>>> Creating a set of %d particles." % n)
        print("     (set SCIPION_TEST_HUGE environment var to other value)")
        
        dbFn = self.getOutputPath('huge_set.sqlite')
        #dbFn = ':memory:'
        
        img = emobj.Particle()
        imgSet = emobj.SetOfParticles(filename=dbFn)
        imgSet.setSamplingRate(1.0)
        
        for i in range(1, n+1):
            # Creating object inside the loop significantly
            # decrease performance
            #img = Particle()
            img.setLocation(i, "images.stk")
            
            imgSet.append(img)
            img.cleanObjId()
            #img.setObjId(None)
            
        imgSet.write()
        
    def test_hugeSetToMd(self):
        """ Just as a bencharmark comparing to test_hugeSet ."""
        # Allow what huge means to be defined with environment var
        n = int(os.environ.get('SCIPION_TEST_HUGE', 10000))
        print(">>>> Creating a set of %d particles." % n)
        print("     (set SCIPION_TEST_HUGE environment var to other value)")
        
        imgMd = md.MetaData()
        
        for i in range(1, n+1):
            # Creating object inside the loop significantly
            # decrease performance
            #img = Particle()
            objId = imgMd.addObject()
            imgMd.setValue(md.MDL_IMAGE, '%06d@images.stk' % (i+1), objId)
            
        mdFn = self.getOutputPath('huge_set.xmd')
        print("Writing metadata to: ", mdFn)
        imgMd.write(mdFn)
        
    def test_hugeSetToText(self):
        """ Just as a bencharmark comparing to test_hugeSet ."""
        # Allow what huge means to be defined with environment var
        n = int(os.environ.get('SCIPION_TEST_HUGE', 10000))
        print(">>>> Creating a set of %d particles." % n)
        print("     (set SCIPION_TEST_HUGE environment var to other value)")
        
        textFn = self.getOutputPath('huge_set.txt')
        print("Writing to text file: ", textFn)
        f = open(textFn, 'w')
        
        for i in range(1, n+1):
            string = '%06d@images.stk' % i
            f.write(string)
            #print >> f, '%06d@images.stk' % i
            
        f.close()     
        
    def test_getFiles(self):
        #create setofImages
        dbFn = self.getOutputPath('multistack_set.sqlite')
        #dbFn = ':memory:'
        n = 10
        m = 3
        img = emobj.Particle()
        imgSet = emobj.SetOfParticles(filename=dbFn)
        imgSet.setSamplingRate(1.0)
        goldStacks = set()

        for j in range(1, m+1):
            stackName = 'stack%02d.stk' % j
            goldStacks.add(stackName)
            for i in range(1, n+1):
                img.setLocation(i, stackName)
                imgSet.append(img)
                img.cleanObjId()

        self.assertEquals(goldStacks, imgSet.getFiles())
        
        imgSet.close()

        # It should automatically call load
        # before accessing items db        
        imgSet.getFirstItem()

    def test_mapper(self):
        """ test that indexes are created when a
        setOfParticles is created """
        PARTNUMBER = 10
        indexesNames = ['_classId', '_micId']
        prot = createDummyProtocol("dummy_protocol")

        # create set of particles
        partSet = prot._createSetOfParticles()
        part = emobj.Particle()
        for i in range(PARTNUMBER+ 1):
            part.setLocation(i, "stack.vol")
            partSet.append(part)
            part.cleanObjId()
        partSet.write()

        # check defined indexes
        setOfPArticleFileName = prot._getPath("particles.sqlite")
        # print os.path.abspath(setOfPArticleFileName)
        indexes = sorted([index[1] for index in
                          getIndex(setOfPArticleFileName)])
        for index, indexName in zip(indexes, indexesNames):
            self.assertEqual(index, 'index_' + indexName )


class TestSetOfCoordinates(BaseTest):
    # TODO: A proper test for setOfCoordinates is missing
    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)

    def test_mapper(self):
        """ test that indexes are created when a
        setOfCoordinates is created """
        PARTNUMBER = 10
        MICNUMBER = 600
        NUMBERCOORDINATES = PARTNUMBER * MICNUMBER
        indexesNames = ['_micId']
        prot = createDummyProtocol("dummy_protocol")

        # create set of micrographs
        micSet = emobj.SetOfMicrographs(filename=":memory:")
        mic = emobj.Micrograph()
        for i in range(NUMBERCOORDINATES):
            mic.setLocation(i, "mic_%06d.mrc" % i)
            micSet.append(mic)
            mic.cleanObjId()
        micSet.write()

        # create a set of particles
        coordSet = prot._createSetOfCoordinates(micSet)
        coord = emobj.Coordinate()
        for i in range(NUMBERCOORDINATES):
            coordSet.append(coord)
            coord.cleanObjId()
        coordSet.write()

        # check defined indexes
        setOfCoordinatesFileName = \
            prot._getPath("coordinates.sqlite")
        print(os.path.abspath(setOfCoordinatesFileName))
        indexes = sorted([index[1] for index in
                          getIndex(setOfCoordinatesFileName)])
        for index, indexName in zip(indexes, indexesNames):
            self.assertEqual(index, 'index_' + indexName )

        # Test speed: based on loop in file protocol_extractparticles.py
        # for 600 mic and 100 part the values for the first
        # second and third  case where:
        # Loop with index: 5 sec
        # Loop no index: 8:01 min
        # Loop optimized code: 4 sec
        # for 6000 mic and 200 part the values for the first
        # Loop with index: 1:47 min
        # optimized Loop with index: 1:20 min
        # Loop no index: after several  hours I stopped the process

        SPEEDTEST = True
        if SPEEDTEST: # code from protocol_particles. line 415
            testTimer = Timer()
            testTimer.tic()
            for mic in micSet:
                micId = mic.getObjId()
                coordList = []
                for coord in coordSet.iterItems(where='_micId=%s' % micId):
                    coordList.append(coord.clone())
            testTimer.toc("Loop with INDEX took:")

            lastMicId = None
            testTimer.tic()
            for coord in coordSet.iterItems(orderBy='_micId',
                                                   direction='ASC'):
                micId = coord.getMicId()
                if micId != lastMicId:
                    lastMicId = micId
                    coordList = []
                coordList.append(coord.clone())
            testTimer.toc("Loop with INDEX and proper code, took:")

            # delete INDEX, this will not work
            # if database is not sqlite
            conn = sqlite3.connect(setOfCoordinatesFileName)
            cur = conn.cursor()
            for index in indexesNames:
                cur.execute("DROP INDEX index_%s" % index)
            cur.close()
            conn.close()

            testTimer.tic()
            for mic in micSet:
                micId = mic.getObjId()
                coordList = []
                for coord in coordSet.iterItems(where='_micId=%s' % micId):
                    coordList.append(coord.clone())
            testTimer.toc("Loop with NO INDEX took:")

            lastMicId = None
            testTimer.tic()
            for coord in coordSet.iterItems(orderBy='_micId',
                                                   direction='ASC'):
                micId = coord.getMicId()
                if micId != lastMicId:
                    lastMicId = micId
                    coordList = []
                coordList.append(coord.clone())
            testTimer.toc("Loop with NO INDEX but proper code, took:")


class TestSetOfClasses2D(BaseTest):

    _labels = [SMALL, WEEKLY]

    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)
        cls.dataset = DataSet.getDataSet('model')  
        cls.selectionFn = cls.dataset.getFile('classesSelection')
        
    def test_basics(self):
        """ Load an existing SetOfClasses and test basic properties 
        such us: _mapperPath, iteration and others.
        """
        classes2DSet = emobj.SetOfClasses2D(filename=self.selectionFn)
        # Check the _mapperPath was properly set
        self.assertEqual(classes2DSet._mapperPath.get(), '%s, ' % self.selectionFn)
        
        cls1 = classes2DSet.getFirstItem()
        self.assertEqual(cls1._mapperPath.get(), '%s,Class001' % self.selectionFn)
        
        img1 = cls1.getFirstItem()
        self.assertEqual(img1.getObjId(), 1) # First image of first class is 1 in this test
        
        images = [[1, 3, 4, 5, 7, 9, 11, 14, 16, 17, 21, 22, 24, 26, 28, 29, 30,
                   35, 37, 38, 39, 40, 42, 45, 54, 57, 62, 65, 67, 69, 70, 71, 74],
                  [2, 8, 10, 12, 13, 15, 19, 20, 23, 25, 27, 33, 34, 41, 43, 44,
                   46, 47, 48, 49, 50, 51, 52, 53, 55, 56, 58, 59, 60, 61, 63,
                   64, 68, 72, 73, 75, 76],
                  [18, 31, 32], 
                  [6, 36, 66]]
        
        classes2DSet.close()
        # Check iteration is working properly even after 
        # a close operation, it should open automatically
        for i, cls in enumerate(classes2DSet):
            l = images[i]
            for j, img in enumerate(cls):
                self.assertEquals(img.getObjId(), l[j])

        for i, rep in enumerate(classes2DSet.iterRepresentatives()):
            self.assertIsNotNone(rep.getLocation())

        # Check the SetOfClasses.iterClassItems method
        allImages = [img for imgList in images for img in imgList]
        idsImages = [img.getObjId()
                     for img in classes2DSet.iterClassItems(iterDisabled=True)]
        self.assertEqual(allImages, idsImages)

    def test_subsetsFromSelection(self):
        """ From a sqlite file of a SetOfClasses2D, with some
        classes and element disabled, we want to create a 
        subset of images and classes.
        """
        classes2DSet = emobj.SetOfClasses2D(filename=self.selectionFn)
        
        imgSet = emobj.SetOfParticles(filename=':memory:')
        # We are going to iterate over the enabled items and create
        # a new set of images
        imgSet.appendFromClasses(classes2DSet)
        # Since we have disabled two classes (6 images) and 1 images
        # from class 1 and 2 (2 images), the final size of the set
        # should be 68
        sizes = [32, 36]
        self.assertEqual(imgSet.getSize(), sum(sizes))
        imgSet.clear() # Close db connection and clean data
        
        # Now create a subset of classes and check the number
        # of images per class
        clsSet = emobj.SetOfClasses2D(filename=':memory:')
        clsSet.appendFromClasses(classes2DSet)
        for i, cls in enumerate(clsSet):
            self.assertEqual(cls.getSize(), sizes[i])
        clsSet.clear() # Close db connection and clean data


class TestTransform(BaseTest):

    def test_scale(self):
        """ Check Scale storage in transformation class
        """
        t = emobj.Transform()
        m = t.getMatrix()
        m[0, 3] = 2
        m[1, 3] = 4
        m[2, 3] = 6
        m[3, 3] = 5
        t.scale(0.5)

        self.assertAlmostEqual(m[0, 3], 1)
        self.assertAlmostEqual(m[1, 3], 2)
        self.assertAlmostEqual(m[2, 3], 3)
        self.assertAlmostEqual(m[3, 3], 1)

    def test_scaleShifts(self):
        """ Check Scale 2D shifts in transformation class
        """
        t = emobj.Transform()
        m = t.getMatrix()
        m[0, 3] = 2
        m[1, 3] = 4
        m[2, 3] = 6
        m[3, 3] = 5
        t.scaleShifts(0.5)

        self.assertAlmostEqual(m[0, 3], 1)
        self.assertAlmostEqual(m[1, 3], 2)
        self.assertAlmostEqual(m[2, 3], 3)
        self.assertAlmostEqual(m[3, 3], 5)

    def test_clone(self):
        """ Check that cloning the Transform will 
        also copy the values of underlying numpy matrix.
        """
        t = emobj.Transform()
        m = t.getMatrix()
        m[0, 3] = 2
        m[1, 3] = 4
        
        t2 = t.clone()
        m2 = t2.getMatrix()
        self.assertTrue(np.allclose(m, m2, rtol=1e-2)) 
        
        p = emobj.Particle()
        p.setTransform(t)
        
        p2 = p.clone()
        m3 = p2.getTransform().getMatrix()
        self.assertTrue(np.allclose(m, m3, rtol=1e-2)) 
        
    
class TestCopyItems(BaseTest):

    _labels = [SMALL, WEEKLY]

    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)
        cls.dataset = DataSet.getDataSet('model')  
        
    def test_listAttribute(self):
        """ 
        Test the use of copyItems function where the items have
        a property that is a list.
        """
        
        inFn = self.dataset.getFile('particles/particles_nma.sqlite')
        outFn = self.getOutputPath('particles.sqlite')

        inputSet = emobj.SetOfParticles(filename=inFn)
        inputSet.setSamplingRate(1.0)
        
        outputSet = emobj.SetOfParticles(filename=outFn)
        outputSet.copyInfo(inputSet)
        
        outputSet.copyItems(inputSet, 
                            updateItemCallback=self._updateItem)
        
        #print("writing particles to: ", outFn)
        outputSet.write()        
        outputSet.close()
        
        # Read again the written set of particles
        checkSet = emobj.SetOfParticles(filename=outFn)
        
        # check that the first item (as the rest)
        # have the added _list attribute with the correct values
        particle = checkSet.getFirstItem()        
        self.assertTrue(particle.hasAttribute('_list'))
        for v1, v2 in izip([1.0, 2.0], particle._list):
            self.assertAlmostEqual(v1, float(v2))
            
        # check that copied items have exactly
        # the same attribes than the input set
        # except for the _list
        for i1, i2 in izip(inputSet, checkSet):
            self.assertTrue(i2.equalAttributes(i1, ignore=['_list']))
        
    def _updateItem(self, item, row):
        item._list = emobj.CsvList()
        item._list.set([1.0, 2.0])


class TestCoordinatesTiltPair(BaseTest):
    # TODO: A proper test for CoordinatesTiltPair is missing
    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)

    def test_mapper(self):
        """ test that indexes are created when a
        setOfCoordinates is created """
        MICNUMBER = 10
        indexesNames = ['_untilted._micId',
                        '_tilted._micId']
        prot = createDummyProtocol("dummy_protocol")

        # create set of untilted and tilted micrographs
        uMicSet = emobj.SetOfMicrographs(filename=":memory:")
        tMicSet = emobj.SetOfMicrographs(filename=":memory:")
        mic = emobj.Micrograph()
        for i in range(MICNUMBER):
            mic.setLocation(i, "umic_%06d.mrc" % i)
            uMicSet.append(mic)
            mic.cleanObjId()
            mic.setLocation(i, "tmic_%06d.mrc" % i)
            tMicSet.append(mic)
            mic.cleanObjId()
        # TODO I do not see any example on how to create
        # a set of CoordinatesTiltPair. I can image
        # that a need to create a set of micTiltPairs
        # and two sets of coordinates but the person who
        # added that data type Should provide a clear test
        # when this is done then I will finish the test_mapper


class TestCoordinatesTiltPair(BaseTest):
    # TODO: A proper test for SetOfMovieParticles is missing
    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)

    def test_mapper(self):
        """ test that indexes are created when a
        SetOfMovieParticles is created """
        # TODO I do not see any example on how to create
        # a set of SetOfMovieParticles. The person who
        # added that data type should provide a clear test
        # when this is done then I will finish the test_mapper
        pass