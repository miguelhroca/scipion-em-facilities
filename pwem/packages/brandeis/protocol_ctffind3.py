# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (jmdelarosa@cnb.csic.es)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'jmdelarosa@cnb.csic.es'
# *
# **************************************************************************
"""
This module contains the protocol for CTF estimation with ctffind3
"""


from pyworkflow.utils.path import makePath, replaceBaseExt, join, basename, cleanPath
from pyworkflow.em import *
from brandeis import *
from convert import parseCtffindOutput
# from pyworkflow.utils.which import which


class ProtBaseCTFFind():
    """ This class cointains the common functionalities for all protocols to
estimate CTF on a set of micrographs using ctffind """
    
    #--------------------------- INFO functions ----------------------------------------------------
    def _validate(self):
        errors = []
        ctffind = join(os.environ['CTFFIND_HOME'], 'ctffind3.exe')
        if not exists(ctffind):
            errors.append('Missing ctffind3.exe')
        return errors
    
    #--------------------------- UTILS functions ---------------------------------------------------
    def _getPsdPath(self, micDir):
        return join(micDir, 'ctffind_psd.mrc')
    
    def _getCtfOutPath(self, micDir):
        return join(micDir, 'ctffind.out')
    
    def _parseOutput(self, filename):
        """ Try to find the output estimation parameters
        from filename. It search for a line containing: Final Values.
        """
        return parseCtffindOutput(filename)
            
    def _getCTFModel(self, defocusU, defocusV, defocusAngle, psdFile):
        ctf = CTFModel()
        ctf.setStandardDefocus(defocusU, defocusV, defocusAngle)
        ctf.setPsdFile(psdFile)
        
        return ctf
    
    def _citations(self):
        return ['Mindell2003']


class ProtCTFFind(ProtBaseCTFFind, ProtCTFMicrographs):
    """Estimates CTF on a set of micrographs
    using the ctffind3 program"""
    _label = 'ctffind3'
    
    #--------------------------- STEPS functions ---------------------------------------------------
    def _estimateCTF(self, micFn, micDir):
        """ Run ctffind3 with required parameters """
        # Create micrograph dir 
        makePath(micDir)
        # Update _params dictionary
        self._params['micFn'] = micFn
        self._params['micDir'] = micDir
        self._params['ctffindOut'] = self._getCtfOutPath(micDir)
        self._params['ctffindPSD'] = self._getPsdPath(micDir)
        self.runJob(self._program, self._args % self._params)
    
    def createOutputStep(self):
        ctfSet = self._createSetOfCTF()
        ctfSet.setMicrographs(self.inputMics)
        defocusList = []
        
        for fn, micDir, mic in self._iterMicrographs():
            out = self._getCtfOutPath(micDir)
            psdFile = self._getPsdPath(micDir)
            result = self._parseOutput(out)
            defocusU, defocusV, defocusAngle = result
            # save the values of defocus for each micrograph in a list
            ctfModel = self._getCTFModel(defocusU, defocusV, defocusAngle, psdFile)
            ctfModel.setMicrograph(mic)
            
            defocusList.append(ctfModel.getDefocusU())
            defocusList.append(ctfModel.getDefocusV())
            ctfSet.append(ctfModel)
        
        self._defocusMaxMin(defocusList)
        self._defineOutputs(outputCTF=ctfSet)
        self._defineCtfRelation(self.inputMics, ctfSet)
    
    #--------------------------- UTILS functions ---------------------------------------------------
    def _prepareCommand(self):
        self._params['step_focus'] = 1000.0
        # Convert digital frequencies to spatial frequencies
        sampling = self.inputMics.getSamplingRate()
        self._params['lowRes'] = sampling / self._params['lowRes']
        self._params['highRes'] = sampling / self._params['highRes']        
        self._program = 'export NATIVEMTZ=kk ; ' + CTFFIND_PATH
        self._args = """   << eof > %(ctffindOut)s
%(micFn)s
%(ctffindPSD)s
%(sphericalAberration)f,%(voltage)f,%(ampContrast)f,%(magnification)f,%(scannedPixelSize)f
%(windowSize)d,%(lowRes)f,%(highRes)f,%(minDefocus)f,%(maxDefocus)f,%(step_focus)f
eof
"""


class ProtRecalculateCTFFind(ProtBaseCTFFind, ProtRecalculateCTF):
    """Re-estimate CTF on a set of micrographs
    using the ctffind3 program"""
    _label = 'ctffind_Recalculate'
    
    def __init__(self, **args):
        ProtRecalculateCTF.__init__(self, **args)
    
    #--------------------------- STEPS functions ---------------------------------------------------
    def _estimateCTF(self, line):
        """ Run ctffind3 with required parameters """
        objId = self._getObjId(line)
        ctfModel = self.setOfCtf.__getitem__(objId)
        
        mic = ctfModel.getMicrograph()
        micFn = mic.getFileName()
        micDir = self._getMicrographDir(mic)
        
        out = self._getCtfOutPath(micDir)
        psdFile = self._getPsdPath(micDir)
        
        cleanPath(out)
        cleanPath(psdFile)
        
        # Update _params dictionary
        self._prepareCommand(line)
        self._params['micFn'] = micFn
        self._params['micDir'] = micDir
        self._params['ctffindOut'] = out
        self._params['ctffindPSD'] = psdFile
        self.runJob(self._program, self._args % self._params)
    
    def createOutputStep(self):
        setOfMics = self.inputCtf.get().getMicrographs()
        outputMics = self._createSetOfMicrographs("_subset")
        outputMics.copyInfo(setOfMics)
        ctfSet = self._createSetOfCTF("_recalculated")
        defocusList = []
        for ctfModel in self.setOfCtf:
            mic = ctfModel.getMicrograph()
            outputMics.append(mic)
            for line in self.values:
                objId = self._getObjId(line)
                
                if objId == ctfModel.getObjId():
                    mic.setObjId(ctfModel.getObjId())
                    micDir = self._getMicrographDir(mic)
                    
                    out = self._getCtfOutPath(micDir)
                    psdFile = self._getPsdPath(micDir)
                    result = self._parseOutput(out)
                    defocusU, defocusV, defocusAngle = result
                    # save the values of defocus for each micrograph in a list
                    ctfModel2 = self._getCTFModel(defocusU, defocusV, defocusAngle, psdFile)
                    ctfModel2.setObjId(mic.getObjId())
                    ctfModel2.setMicrograph(mic)
                    ctfModel.copy(ctfModel2)
                    
                    # save the values of defocus for each micrograph in a list
                    defocusList.append(ctfModel2.getDefocusU())
                    defocusList.append(ctfModel2.getDefocusV())
                    break
            ctfSet.append(ctfModel)
        
        self.setOfCtf.close()
        ctfSet.setMicrographs(outputMics)
        
        self._defineOutputs(outputMicrographs=outputMics)
        self._defineOutputs(outputCTF=ctfSet)
        
        self._defineTransformRelation(setOfMics, outputMics)
        self._defineSourceRelation(self.inputCtf.get(), ctfSet)
        self._defocusMaxMin(defocusList)
        self._ctfCounter(defocusList)
    
    #--------------------------- UTILS functions ---------------------------------------------------
    def _prepareCommand(self, line):
        
        self._defineValues(line)
        # get the size and the image of psd
        objId = self._getObjId(line)
        ctfModel = self.setOfCtf.__getitem__(objId)
        imgPsd = ctfModel.getPsdFile()
        imgh = ImageHandler()
        size, _, _, _ = imgh.getDimensions(imgPsd)
        
        mic = ctfModel.getMicrograph()
        micDir = self._getMicrographDir(mic)
        
        # Convert digital frequencies to spatial frequencies
        sampling = mic.getSamplingRate()
        self._params['step_focus'] = 1000.0
        self._params['lowRes'] = sampling / float(line[4])
        self._params['highRes'] = sampling / float(line[5])
        self._params['minDefocus'] = min([float(line[1]), float(line[2])])
        self._params['maxDefocus'] = max([float(line[1]), float(line[2])])
        self._params['windowSize'] = size
        
        self._program = 'export NATIVEMTZ=kk ; ' + CTFFIND_PATH
        self._args = """   << eof > %(ctffindOut)s
%(micFn)s
%(ctffindPSD)s
%(sphericalAberration)f,%(voltage)f,%(ampContrast)f,%(magnification)f,%(scannedPixelSize)f
%(windowSize)d,%(lowRes)f,%(highRes)f,%(minDefocus)f,%(maxDefocus)f,%(step_focus)f
eof
"""
    
    