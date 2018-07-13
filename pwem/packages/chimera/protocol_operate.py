# **************************************************************************
# *
# * Authors:     Grigory Sharov (sharov@igbmc.fr)
# *              Marta Martinez (mmmtnez@cnb.csic.es)
# *              Roberto Marabini (roberto@cnb.csic.es)
# *
# * L'Institut de genetique et de biologie moleculaire et cellulaire (IGBMC)
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
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import os
from pyworkflow import VERSION_1_2
from pyworkflow.em import PdbFile
from pyworkflow.em import Volume
from pyworkflow.em.convert import ImageHandler
from pyworkflow.em.protocol import EMProtocol
from pyworkflow.em.header_handler.CCP4.convert import Ccp4Header
from pyworkflow.em.viewers.chimera_utils import \
    createCoordinateAxisFile, getProgram, runChimeraProgram,\
    chimeraPdbTemplateFileName, chimeraMapTemplateFileName, \
    chimeraScriptFileName, sessionFile

from pyworkflow.protocol.params import MultiPointerParam, PointerParam, \
    StringParam
from pyworkflow.utils.properties import Message
from pyworkflow.em.packages.chimera.protocol_base import ChimeraProtBase

class ChimeraProtOperate(ChimeraProtBase):
    """Protocol to perform rigid fit using Chimera.
        Execute command *scipionwrite [model #n] [refmodel #p]
        [saverefmodel 0|1]* from command line in order to transferm fitted
        pdb to scipion. Default values are model=#0,
        refmodel =#1 and saverefmodel 0 (false).
        model refers to the pdb file. refmodel to a 3Dmap"""
    _label = 'chimera operate'