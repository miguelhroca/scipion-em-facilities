# **************************************************************************
# *
# * Authors:     Pablo Conesa (pconesa@cnb.csic.es)
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
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************
from pyworkflow.utils import createLink
import pyworkflow as pw
import pwem
import os

LIB = "lib"

ghostStr = """
 >>> WARNING: Image library not found!
  > Please install Xmipp to get full functionality. 
(Configuration->Plugins->scipion-em-xmipp -> expand, in Scipion plugin manager window)\n
"""
def linkXmippBinding():
    xmipp_home = pwem.Config.XMIPP_HOME
    # If exists xmipp
    if os.path.exists(xmipp_home):

        # Link the binding
        xmippBindingPath = os.path.join(xmipp_home,"bindings", "python", "xmippLib.so")
        dest = os.path.join(pw.Config.SCIPION_BINDINGS, "xmippLib.so")
        if not os.path.exists(dest):
            createLink(xmippBindingPath, dest)

            xmippLibFolder = os.path.join(xmipp_home, "lib")

            # Link the libraries
            createLink(os.path.join(xmippLibFolder, "libXmipp.so"),
                   os.path.join(pw.Config.SCIPION_LIBS, "libXmipp.so"))
            createLink(os.path.join(xmippLibFolder, "libXmippCore.so"),
                   os.path.join(pw.Config.SCIPION_LIBS, "libXmippCore.so"))

            print("Xmipp bindings registered in Scipion. You will need to restart.")

        if os.path.abspath(pw.Config.SCIPION_LIBS) not in os.environ.get("LD_LIBRARY_PATH", ""):
            print("LD_LIBRARY_PATH must contain scipion lib folder (%s).  Please, add it." % os.path.abspath(pw.Config.SCIPION_LIBS))


print(ghostStr)

linkXmippBinding()

GHOST_ACTIVATED = True  # Flag to unequivocal identify the Ghost

DT_DEFAULT = None
DT_UNKNOWN = None
DT_UCHAR = None
DT_SCHAR = None
DT_USHORT = None
DT_SHORT = None
DT_UINT = None
DT_INT = None
DT_LONG = None
DT_FLOAT = None
DT_DOUBLE = None
DT_COMPLEXSHORT = None
DT_COMPLEXINT = None
DT_COMPLEXFLOAT = None
DT_COMPLEXDOUBLE = None
DT_BOOL = None
DT_LASTENTRY = None

AGGR_COUNT = None
AGGR_MAX = None
AGGR_SUM = None
AGGR_AVG = None
AGGR_MIN = None

UNION = None
UNION_DISTINCT = None
INTERSECTION = None
SUBSTRACTION = None
INNER_JOIN = None
LEFT_JOIN = None
NATURAL_JOIN = None
OUTER_JOIN = None
INNER = None
LEFT = None
OUTER = None
NATURAL = None

EQ = None
NE = None
GT = None
LT = None
GE = None
LE = None

MD_OVERWRITE = None
MD_APPEND = None
MDL_UNDEFINED = None
MDL_FIRST_LABEL = None
MDL_OBJID = None
MDL_ANGLE_PSI2 = None
MDL_ANGLE_PSI = None

MDL_ANGLE_PSI_DIFF = None
MDL_ANGLE_ROT2 = None
MDL_ANGLE_ROT = None
MDL_ANGLE_ROT_DIFF = None
MDL_ANGLE_TILT2 = None
MDL_ANGLE_TILT = None
MDL_ANGLE_TILT_DIFF = None
MDL_ANGLE_DIFF = None
MDL_ANGLE_Y = None
MDL_ANGLE_Y2 = None
MDL_AVG = None
MDL_AVG_CHANGES_ORIENTATIONS = None
MDL_AVG_CHANGES_OFFSETS = None
MDL_AVG_CHANGES_CLASSES = None

MDL_BGMEAN = None
MDL_BLOCK_NUMBER = None

MDL_CLASS_COUNT = None
MDL_CLASS_PERCENTAGE = None
MDL_CLASSIFICATION_DATA = None
MDL_CLASSIFICATION_DATA_SIZE = None
MDL_CLASSIFICATION_DPR_05 = None
MDL_CLASSIFICATION_FRC_05 = None
MDL_CLASSIFICATION_INTRACLASS_DISTANCE = None

MDL_COLOR = None
MDL_COMMENT = None
MDL_CONTINUOUS_GRAY_A = None
MDL_CONTINUOUS_GRAY_B = None
MDL_CONTINUOUS_X = None
MDL_CONTINUOUS_Y = None
MDL_COST = None
MDL_COUNT = None
MDL_COUNT2 = None
MDL_CRYSTAL_LATTICE_A = None
MDL_CRYSTAL_LATTICE_B = None
MDL_CRYSTAL_DISAPPEAR_THRE = None
MDL_CRYSTAL_SHFILE = None
MDL_CRYSTAL_ORTHO_PRJ = None
MDL_CRYSTAL_PROJ = None
MDL_CRYSTAL_CELLX = None
MDL_CRYSTAL_CELLY = None
MDL_CRYSTAL_SHIFTX = None
MDL_CRYSTAL_SHIFTY = None
MDL_CRYSTAL_SHIFTZ = None
MDL_CTF_INPUTPARAMS = None
MDL_CTF_MODEL = None
MDL_CTF_MODEL2 = None
MDL_CTF_SAMPLING_RATE = None
MDL_CTF_VOLTAGE = None
MDL_CTF_DEFOCUSU = None
MDL_CTF_DEFOCUSV = None
MDL_CTF_DEFOCUS_ANGLE = None
MDL_CTF_DOWNSAMPLE_PERFORMED = None
MDL_CTF_CS = None
MDL_CTF_CA = None
MDL_CTF_GROUP = None
MDL_CTF_ENERGY_LOSS = None
MDL_CTF_LENS_STABILITY = None
MDL_CTF_CONVERGENCE_CONE = None
MDL_CTF_LONGITUDINAL_DISPLACEMENT = None
MDL_CTF_TRANSVERSAL_DISPLACEMENT = None
MDL_CTF_Q0 = None
MDL_CTF_K = None
MDL_CTF_BG_GAUSSIAN_K = None
MDL_CTF_BG_GAUSSIAN_SIGMAU = None
MDL_CTF_BG_GAUSSIAN_SIGMAV = None
MDL_CTF_BG_GAUSSIAN_CU = None
MDL_CTF_BG_GAUSSIAN_CV = None
MDL_CTF_BG_GAUSSIAN_ANGLE = None
MDL_CTF_BG_SQRT_K = None
MDL_CTF_BG_SQRT_U = None
MDL_CTF_BG_SQRT_V = None
MDL_CTF_BG_SQRT_ANGLE = None
MDL_CTF_BG_BASELINE = None
MDL_CTF_BG_GAUSSIAN2_K = None
MDL_CTF_BG_GAUSSIAN2_SIGMAU = None
MDL_CTF_BG_GAUSSIAN2_SIGMAV = None
MDL_CTF_BG_GAUSSIAN2_CU = None
MDL_CTF_BG_GAUSSIAN2_CV = None
MDL_CTF_BG_GAUSSIAN2_ANGLE = None
MDL_CTF_CRIT_PSDCORRELATION90 = None
MDL_CTF_CRIT_FIRSTZERORATIO = None
MDL_CTF_CRIT_FIRSTZEROAVG = None
MDL_CTF_CRIT_FIRSTZERODISAGREEMENT = None
MDL_CTF_CRIT_NORMALITY = None
MDL_CTF_CRIT_DAMPING = None
MDL_CTF_CRIT_PSDRADIALINTEGRAL = None
MDL_CTF_CRIT_FITTINGSCORE = None
MDL_CTF_CRIT_FITTINGCORR13 = None
MDL_CTF_CRIT_ICENESS = None
MDL_CTF_CRIT_PSDVARIANCE = None
MDL_CTF_CRIT_PSDPCA1VARIANCE = None
MDL_CTF_CRIT_PSDPCARUNSTEST = None
MDL_CTF_PHASE_SHIFT = None
MDL_CTF_VPP_RADIUS = None
MDL_CUMULATIVE_SSNR = None
MDL_CTF_CRIT_MAXFREQ = None

MDL_DATATYPE = None
MDL_DATE = None
MDL_DEFGROUP = None
MDL_DIMENSIONS_3D = None
MDL_DIMENSIONS_2D = None
MDL_DM3_IDTAG = None
MDL_DM3_NODEID = None
MDL_DM3_NUMBER_TYPE = None
MDL_DM3_PARENTID = None
MDL_DM3_TAGCLASS = None
MDL_DM3_TAGNAME = None
MDL_DM3_SIZE = None
MDL_DM3_VALUE = None

MDL_ENABLED = None

MDL_FLIP = None
MDL_FOM = None
MDL_FRAME_ID = None

MDL_GATHER_ID = None

MDL_IDX = None
MDL_IMAGE = None
MDL_IMAGE_COVARIANCE = None
MDL_IMAGE_IDX = None
MDL_IMAGE_ORIGINAL = None
MDL_IMAGE_REF = None
MDL_IMAGE_RESIDUAL = None
MDL_IMAGE_TILTED = None
MDL_IMGMD = None
MDL_IMAGE1 = None
MDL_IMAGE2 = None
MDL_IMAGE3 = None
MDL_IMAGE4 = None
MDL_IMAGE5 = None
MDL_INTSCALE = None
MDL_ITEM_ID = None
MDL_ITER = None
MDL_KSTEST = None
MDL_LL = None
MDL_MACRO_CMD = None
MDL_MACRO_CMD_ARGS = None
MDL_MAGNIFICATION = None
MDL_MASK = None
MDL_MAXCC = None
MDL_MAX = None
MDL_MICROGRAPH = None
MDL_MICROGRAPH_ID = None
MDL_MICROGRAPH_MOVIE = None
MDL_MICROGRAPH_MOVIE_ID = None
MDL_MICROGRAPH_PARTICLES = None
MDL_MICROGRAPH_ORIGINAL = None
MDL_MICROGRAPH_TILTED = None
MDL_MICROGRAPH_TILTED_ORIGINAL = None
MDL_MIN = None
MDL_MIRRORFRAC = None
MDL_MISSINGREGION_NR = None
MDL_MISSINGREGION_TYPE = None
MDL_MISSINGREGION_THY0 = None
MDL_MISSINGREGION_THYF = None
MDL_MISSINGREGION_THX0 = None
MDL_MISSINGREGION_THXF = None
MDL_MLF_CTF = None
MDL_MLF_WIENER = None
MDL_MLF_SIGNAL = None
MDL_MLF_NOISE = None
MDL_MODELFRAC = None

MDL_NEIGHBORS = None
MDL_NEIGHBOR = None
MDL_NEIGHBORHOOD_RADIUS = None
MDL_NMA = None
MDL_NMA_MODEFILE = None
MDL_NMA_COLLECTIVITY = None
MDL_NMA_MINRANGE = None
MDL_NMA_MAXRANGE = None
MDL_NMA_SCORE = None
MDL_NMA_ATOMSHIFT = None
MDL_NOISE_ANGLES = None
MDL_NOISE_PARTICLE_COORD = None
MDL_NOISE_COORD = None
MDL_NOISE_PIXEL_LEVEL = None

MDL_OPTICALFLOW_MEANX = None
MDL_OPTICALFLOW_MEANY = None
MDL_OPTICALFLOW_STDX = None
MDL_OPTICALFLOW_STDY = None

MDL_ORDER = None
MDL_ORIGIN_X = None
MDL_ORIGIN_Y = None
MDL_ORIGIN_Z = None

MDL_PARTICLE_ID = None
MDL_PICKING_AUTOPICKPERCENT = None
MDL_PICKING_PARTICLE_SIZE = None
MDL_PICKING_STATE = None
MDL_PICKING_MICROGRAPH_STATE = None
MDL_PICKING_TEMPLATES = None
MDL_PICKING_MANUALPARTICLES_SIZE = None
MDL_PICKING_AUTOPARTICLES_SIZE = None
MDL_PMAX = None
MDL_AVGPMAX = None
MDL_PROGRAM = None
MDL_PRJ_DIMENSIONS = None
MDL_PRJ_ANGFILE = None
MDL_PRJ_PSI_NOISE = None
MDL_PRJ_PSI_RANDSTR = None
MDL_PRJ_PSI_RANGE = None
MDL_PRJ_ROT_NOISE = None
MDL_PRJ_ROT_RANDSTR = None
MDL_PRJ_ROT_RANGE = None
MDL_PRJ_TILT_NOISE = None
MDL_PRJ_TILT_RANDSTR = None
MDL_PRJ_TILT_RANGE = None
MDL_PRJ_VOL = None
MDL_PSD = None
MDL_PSD_ENHANCED = None

MDL_RANDOMSEED = None
MDL_REF3D = None
MDL_REF = None
MDL_REFMD = None
MDL_RESOLUTION_DPR = None
MDL_RESOLUTION_ERRORL2 = None
MDL_RESOLUTION_FRC = None
MDL_RESOLUTION_FRCRANDOMNOISE = None
MDL_RESOLUTION_FREQ = None
MDL_RESOLUTION_FREQREAL = None
MDL_RESOLUTION_LOG_STRUCTURE_FACTOR = None
MDL_RESOLUTION_SSNR = None
MDL_RESOLUTION_STRUCTURE_FACTOR = None
MDL_RESOLUTION_RFACTOR = None

MDL_SAMPLINGRATE = None
MDL_SAMPLINGRATE_ORIGINAL = None
MDL_SAMPLINGRATE_X = None
MDL_SAMPLINGRATE_Y = None
MDL_SAMPLINGRATE_Z = None
MDL_SCALE = None
MDL_SELFILE = None
MDL_SERIE = None
MDL_SHIFT_X = None
MDL_SHIFT_Y = None
MDL_SHIFT_Z = None
MDL_SHIFT_X2 = None
MDL_SHIFT_Y2 = None
MDL_SHIFT_X_DIFF = None
MDL_SHIFT_Y_DIFF = None
MDL_SHIFT_DIFF = None
MDL_SIGMANOISE = None
MDL_SIGMAOFFSET = None
MDL_SIGNALCHANGE = None
MDL_STAR_COMMENT = None
MDL_STDDEV = None
MDL_SCORE_BY_ALIGNABILITY_PRECISION = None
MDL_SCORE_BY_ALIGNABILITY_ACCURACY = None
MDL_SCORE_BY_MIRROR = None
MDL_SCORE_BY_ALIGNABILITY_PRECISION_EXP = None
MDL_SCORE_BY_ALIGNABILITY_PRECISION_REF = None
MDL_SCORE_BY_ALIGNABILITY_ACCURACY_EXP = None
MDL_SCORE_BY_ALIGNABILITY_ACCURACY_REF = None
MDL_SCORE_BY_ALIGNABILITY_NOISE = None
MDL_SCORE_BY_EMPTINESS = None
MDL_SCORE_BY_ENTROPY = None
MDL_SCORE_BY_GRANULO = None
MDL_SCORE_BY_GINI = None
MDL_SCORE_BY_LBP = None
MDL_SCORE_BY_PCA_RESIDUAL = None
MDL_SCORE_BY_PCA_RESIDUAL_PROJ = None
MDL_SCORE_BY_PCA_RESIDUAL_EXP = None
MDL_SCORE_BY_SCREENING = None
MDL_SCORE_BY_VARIANCE = None
MDL_SCORE_BY_VAR = None
MDL_SCORE_BY_ZERNIKE = None
MDL_SCORE_BY_ZSCORE = None

MDL_SUM = None
MDL_SUMWEIGHT = None
MDL_SYMNO = None

MDL_TIME = None
MDL_TRANSFORM_MATRIX = None
MDL_TOMOGRAM_VOLUME = None
MDL_TOMOGRAMMD = None

MDL_USER = None

MDL_VOLUME_SCORE_SUM = None
MDL_VOLUME_SCORE_SUM_TH = None
MDL_VOLUME_SCORE_MEAN = None
MDL_VOLUME_SCORE_MIN = None
MDL_VOLUME_SCORE1 = None
MDL_VOLUME_SCORE2 = None
MDL_VOLUME_SCORE3 = None
MDL_VOLUME_SCORE4 = None

MDL_WEIGHT = None
MDL_WEIGHT_PRECISION_ALIGNABILITY = None
MDL_WEIGHT_ACCURACY_ALIGNABILITY = None
MDL_WEIGHT_ALIGNABILITY = None
MDL_WEIGHT_PRECISION_MIRROR = None
MDL_WEIGHT_P = None

MDL_WROBUST = None

MDL_XCOOR = None
MDL_XCOOR_TILT = None
MDL_XSIZE = None
MDL_X = None

MDL_YCOOR = None
MDL_YCOOR_TILT = None
MDL_Y = None
MDL_YSIZE = None
MDL_ZCOOR = None
MDL_Z = None
MDL_ZSCORE = None
MDL_ZSCORE_HISTOGRAM = None
MDL_ZSCORE_RESMEAN = None
MDL_ZSCORE_RESVAR = None
MDL_ZSCORE_RESCOV = None
MDL_ZSCORE_SHAPE1 = None
MDL_ZSCORE_SHAPE2 = None
MDL_ZSCORE_SNR1 = None
MDL_ZSCORE_SNR2 = None
MDL_ZSIZE = None
MDL_LAST_LABEL = None

# ----- Label types ------
LABEL_NOTYPE = None
LABEL_INT = None
LABEL_BOOL = None
LABEL_DOUBLE = None
LABEL_VECTOR_DOUBLE = None
LABEL_STRING = None
LABEL_SIZET = None
LABEL_VECTOR_SIZET = None
TAGLABEL_NOTAG = None
TAGLABEL_TEXTFILE = None
TAGLABEL_METADATA = None
TAGLABEL_CTFPARAM = None
TAGLABEL_IMAGE = None
TAGLABEL_VOLUME = None
TAGLABEL_STACK = None
TAGLABEL_MICROGRAPH = None
TAGLABEL_PSD = None

# ----- RELION labels -------
RLN_AREA_ID = None
RLN_AREA_NAME = None
RLN_COMMENT = None

RLN_CTF_BFACTOR = None
RLN_CTF_SCALEFACTOR = None
RLN_CTF_SAMPLING_RATE = None
RLN_CTF_VOLTAGE = None
RLN_CTF_DEFOCUSU = None
RLN_CTF_DEFOCUSV = None
RLN_CTF_DEFOCUS_ANGLE = None
RLN_CTF_CS = None
RLN_CTF_CA = None
RLN_CTF_DETECTOR_PIXEL_SIZE = None
RLN_CTF_ENERGY_LOSS = None
RLN_CTF_FOM = None
RLN_CTF_IMAGE = None
RLN_CTF_LENS_STABILITY = None
RLN_CTF_MAGNIFICATION = None
RLN_CTF_CONVERGENCE_CONE = None
RLN_CTF_LONGITUDINAL_DISPLACEMENT = None
RLN_CTF_TRANSVERSAL_DISPLACEMENT = None
RLN_CTF_Q0 = None
RLN_CTF_K = None
RLN_CTF_VALUE = None
RLN_CTF_PHASESHIFT = None

RLN_IMAGE_NAME = None
RLN_IMAGE_RECONSTRUCT_NAME = None
RLN_IMAGE_ID = None
RLN_IMAGE_ENABLED = None
RLN_IMAGE_DATATYPE = None
RLN_IMAGE_DIMENSIONALITY = None
RLN_IMAGE_BEAMTILT_X = None
RLN_IMAGE_BEAMTILT_Y = None
RLN_IMAGE_BEAMTILT_GROUP = None
RLN_IMAGE_COORD_X = None
RLN_IMAGE_COORD_Y = None
RLN_IMAGE_COORD_Z = None
RLN_IMAGE_FRAME_NR = None
RLN_IMAGE_MAGNIFICATION_CORRECTION = None
RLN_IMAGE_NORM_CORRECTION = None
RLN_IMAGE_SAMPLINGRATE = None
RLN_IMAGE_SAMPLINGRATE_X = None
RLN_IMAGE_SAMPLINGRATE_Y = None
RLN_IMAGE_SAMPLINGRATE_Z = None
RLN_IMAGE_SIZE = None
RLN_IMAGE_SIZEX = None
RLN_IMAGE_SIZEY = None
RLN_IMAGE_SIZEZ = None
RLN_IMAGE_STATS_MIN = None
RLN_IMAGE_STATS_MAX = None
RLN_IMAGE_STATS_AVG = None
RLN_IMAGE_STATS_STDDEV = None
RLN_IMAGE_STATS_SKEW = None
RLN_IMAGE_STATS_KURT = None
RLN_IMAGE_WEIGHT = None

RLN_MATRIX_1_1 = None
RLN_MATRIX_1_2 = None
RLN_MATRIX_1_3 = None
RLN_MATRIX_2_1 = None
RLN_MATRIX_2_2 = None
RLN_MATRIX_2_3 = None
RLN_MATRIX_3_1 = None
RLN_MATRIX_3_2 = None
RLN_MATRIX_3_3 = None

RLN_MICROGRAPH_ID = None
RLN_MICROGRAPH_MOVIE_NAME = None
RLN_MICROGRAPH_NAME = None
RLN_MICROGRAPH_TILT_ANGLE = None
RLN_MICROGRAPH_TILT_AXIS_DIRECTION = None
RLN_MICROGRAPH_TILT_AXIS_OUTOFPLANE = None

RLN_MLMODEL_ACCURACY_ROT = None
RLN_MLMODEL_ACCURACY_TRANS = None
RLN_MLMODEL_AVE_PMAX = None
RLN_MLMODEL_CURRENT_RESOLUTION = None
RLN_MLMODEL_CURRENT_SIZE = None
RLN_MLMODEL_DATA_VS_PRIOR_REF = None
RLN_MLMODEL_DIMENSIONALITY = None
RLN_MLMODEL_DIMENSIONALITY_DATA = None
RLN_MLMODEL_DIFF2_HALVES_REF = None
RLN_MLMODEL_FSC_HALVES_REF = None
RLN_MLMODEL_GROUP_NAME = None
RLN_MLMODEL_GROUP_NO = None
RLN_MLMODEL_GROUP_NR_PARTICLES = None
RLN_MLMODEL_GROUP_SCALE_CORRECTION = None
RLN_MLMODEL_INTERPOLATOR = None
RLN_MLMODEL_LL = None
RLN_MLMODEL_MINIMUM_RADIUS_NN_INTERPOLATION = None
RLN_MLMODEL_NORM_CORRECTION_AVG = None
RLN_MLMODEL_NR_CLASSES = None
RLN_MLMODEL_NR_GROUPS = None
RLN_MLMODEL_ORIGINAL_SIZE = None
RLN_MLMODEL_ORIENTABILITY_CONTRIBUTION = None
RLN_MLMODEL_PADDING_FACTOR = None
RLN_MLMODEL_PDF_CLASS = None
RLN_MLMODEL_PRIOR_OFFX_CLASS = None
RLN_MLMODEL_PRIOR_OFFY_CLASS = None
RLN_MLMODEL_PDF_ORIENT = None
RLN_MLMODEL_PIXEL_SIZE = None
RLN_MLMODEL_POWER_REF = None
RLN_MLMODEL_PRIOR_MODE = None
RLN_MLMODEL_SIGMA_OFFSET = None
RLN_MLMODEL_SIGMA_ROT = None
RLN_MLMODEL_SIGMA_TILT = None
RLN_MLMODEL_SIGMA_PSI = None
RLN_MLMODEL_REF_IMAGE = None
RLN_MLMODEL_SIGMA2_NOISE = None
RLN_MLMODEL_SIGMA2_REF = None
RLN_MLMODEL_SSNR_REF = None
RLN_MLMODEL_TAU2_FUDGE_FACTOR = None
RLN_MLMODEL_TAU2_REF = None
RLN_OPTIMISER_ACCURACY_ROT = None
RLN_OPTIMISER_ACCURACY_TRANS = None
RLN_OPTIMISER_ADAPTIVE_FRACTION = None
RLN_OPTIMISER_ADAPTIVE_OVERSAMPLING = None
RLN_OPTIMISER_AUTO_LOCAL_HP_ORDER = None
RLN_OPTIMISER_AVAILABLE_MEMORY = None
RLN_OPTIMISER_BEST_RESOL_THUS_FAR = None
RLN_OPTIMISER_CHANGES_OPTIMAL_OFFSETS = None
RLN_OPTIMISER_CHANGES_OPTIMAL_ORIENTS = None
RLN_OPTIMISER_CHANGES_OPTIMAL_CLASSES = None
RLN_OPTIMISER_COARSE_SIZE = None
RLN_OPTIMISER_DATA_ARE_CTF_PHASE_FLIPPED = None
RLN_OPTIMISER_DATA_STARFILE = None
RLN_OPTIMISER_DO_AUTO_REFINE = None
RLN_OPTIMISER_DO_ONLY_FLIP_CTF_PHASES = None
RLN_OPTIMISER_DO_CORRECT_CTF = None
RLN_OPTIMISER_DO_CORRECT_MAGNIFICATION = None
RLN_OPTIMISER_DO_CORRECT_NORM = None
RLN_OPTIMISER_DO_CORRECT_SCALE = None
RLN_OPTIMISER_DO_REALIGN_MOVIES = None
RLN_OPTIMISER_DO_MAP = None
RLN_OPTIMISER_DO_SOLVENT_FLATTEN = None
RLN_OPTIMISER_DO_SKIP_ALIGN = None
RLN_OPTIMISER_DO_SKIP_ROTATE = None
RLN_OPTIMISER_DO_SPLIT_RANDOM_HALVES = None
RLN_OPTIMISER_DO_ZERO_MASK = None
RLN_OPTIMISER_FIX_SIGMA_NOISE = None
RLN_OPTIMISER_FIX_SIGMA_OFFSET = None
RLN_OPTIMISER_FIX_TAU = None
RLN_OPTIMISER_HAS_CONVERGED = None
RLN_OPTIMISER_HAS_HIGH_FSC_AT_LIMIT = None
RLN_OPTIMISER_HAS_LARGE_INCR_SIZE_ITER_AGO = None
RLN_OPTIMISER_HIGHRES_LIMIT_EXP = None
RLN_OPTIMISER_IGNORE_CTF_UNTIL_FIRST_PEAK = None
RLN_OPTIMISER_INCR_SIZE = None
RLN_OPTIMISER_ITERATION_NO = None
RLN_OPTIMISER_LOWRES_JOIN_RANDOM_HALVES = None
RLN_OPTIMISER_MAGNIFICATION_RANGE = None
RLN_OPTIMISER_MAGNIFICATION_STEP = None
RLN_OPTIMISER_MAX_COARSE_SIZE = None
RLN_OPTIMISER_MAX_NR_POOL = None
RLN_OPTIMISER_MODEL_STARFILE = None
RLN_OPTIMISER_MODEL_STARFILE2 = None
RLN_OPTIMISER_NR_ITERATIONS = None
RLN_OPTIMISER_NR_ITER_WO_RESOL_GAIN = None
RLN_OPTIMISER_NR_ITER_WO_HIDDEN_VAR_CHANGES = None
RLN_OPTIMISER_OUTPUT_ROOTNAME = None
RLN_OPTIMISER_PARTICLE_DIAMETER = None
RLN_OPTIMISER_RADIUS_MASK_3D_MAP = None
RLN_OPTIMISER_RADIUS_MASK_EXP_PARTICLES = None
RLN_OPTIMISER_RANDOM_SEED = None
RLN_OPTIMISER_REFS_ARE_CTF_CORRECTED = None
RLN_OPTIMISER_SAMPLING_STARFILE = None
RLN_OPTIMISER_SMALLEST_CHANGES_OPT_CLASSES = None
RLN_OPTIMISER_SMALLEST_CHANGES_OPT_OFFSETS = None
RLN_OPTIMISER_SMALLEST_CHANGES_OPT_ORIENTS = None
RLN_OPTIMISER_SOLVENT_MASK_NAME = None
RLN_OPTIMISER_SOLVENT_MASK2_NAME = None
RLN_OPTIMISER_TAU_SPECTRUM_NAME = None
RLN_OPTIMISER_USE_TOO_COARSE_SAMPLING = None
RLN_OPTIMISER_WIDTH_MASK_EDGE = None
RLN_ORIENT_FLIP = None
RLN_ORIENT_ID = None
RLN_ORIENT_ORIGIN_X = None
RLN_ORIENT_ORIGIN_X_PRIOR = None
RLN_ORIENT_ORIGIN_Y = None
RLN_ORIENT_ORIGIN_Y_PRIOR = None
RLN_ORIENT_ORIGIN_Z = None
RLN_ORIENT_ORIGIN_Z_PRIOR = None
RLN_ORIENT_ROT = None
RLN_ORIENT_ROT_PRIOR = None
RLN_ORIENT_TILT = None
RLN_ORIENT_TILT_PRIOR = None
RLN_ORIENT_PSI = None
RLN_ORIENT_PSI_PRIOR = None
RLN_ORIENT_PSI_PRIOR_FLIP_RATIO = None
RLN_PARTICLE_AUTOPICK_FOM = None
RLN_PARTICLE_CLASS = None
RLN_PARTICLE_DLL = None
RLN_PARTICLE_ID = None
RLN_PARTICLE_FOM = None
RLN_PARTICLE_KL_DIVERGENCE = None
RLN_PARTICLE_MOVIE_RUNNING_AVG = None
RLN_PARTICLE_RANDOM_SUBSET = None
RLN_PARTICLE_NAME = None
RLN_PARTICLE_ORI_NAME = None
RLN_PARTICLE_NR_SIGNIFICANT_SAMPLES = None
RLN_PARTICLE_NR_FRAMES = None
RLN_PARTICLE_NR_FRAMES_AVG = None
RLN_PARTICLE_PMAX = None

# New helical labes in Relion 2.x
RLN_MLMODEL_HELICAL_NR_ASU = None
RLN_MLMODEL_HELICAL_TWIST = None
RLN_MLMODEL_HELICAL_TWIST_MIN = None
RLN_MLMODEL_HELICAL_TWIST_MAX = None
RLN_MLMODEL_HELICAL_TWIST_INITIAL_STEP = None
RLN_MLMODEL_HELICAL_RISE = None
RLN_MLMODEL_HELICAL_RISE_MIN = None
RLN_MLMODEL_HELICAL_RISE_MAX = None
RLN_MLMODEL_HELICAL_RISE_INITIAL_STEP = None
RLN_OPTIMISER_DO_HELICAL_REFINE = None
RLN_OPTIMISER_HELICAL_TWIST_INITIAL = None
RLN_OPTIMISER_HELICAL_RISE_INITIAL = None
RLN_OPTIMISER_HELICAL_Z_PERCENTAGE = None
RLN_OPTIMISER_HELICAL_TUBE_INNER_DIAMETER = None
RLN_OPTIMISER_HELICAL_TUBE_OUTER_DIAMETER = None
RLN_OPTIMISER_HELICAL_SYMMETRY_LOCAL_REFINEMENT = None
RLN_OPTIMISER_HELICAL_SIGMA_DISTANCE = None
RLN_OPTIMISER_IGNORE_HELICAL_SYMMETRY = None
RLN_OPTIMISER_HELICAL_KEEP_TILT_PRIOR_FIXED = None
RLN_PARTICLE_HELICAL_TUBE_ID = None
RLN_PARTICLE_HELICAL_TUBE_PITCH = None
RLN_PARTICLE_HELICAL_TRACK_LENGTH = None
RLN_SAMPLING_HELICAL_OFFSET_STEP = None

RLN_POSTPROCESS_BFACTOR = None
RLN_POSTPROCESS_FINAL_RESOLUTION = None
RLN_POSTPROCESS_FSC_TRUE = None
RLN_POSTPROCESS_FSC_MASKED = None
RLN_POSTPROCESS_FSC_UNMASKED = None
RLN_POSTPROCESS_FSC_RANDOM_MASKED = None
RLN_POSTPROCESS_GUINIER_FIT_CORRELATION = None
RLN_POSTPROCESS_GUINIER_FIT_INTERCEPT = None
RLN_POSTPROCESS_GUINIER_FIT_SLOPE = None
RLN_POSTPROCESS_GUINIER_VALUE_IN = None
RLN_POSTPROCESS_GUINIER_VALUE_INVMTF = None
RLN_POSTPROCESS_GUINIER_VALUE_WEIGHTED = None
RLN_POSTPROCESS_GUINIER_VALUE_SHARPENED = None
RLN_POSTPROCESS_GUINIER_VALUE_INTERCEPT = None
RLN_POSTPROCESS_GUINIER_RESOL_SQUARED = None
RLN_POSTPROCESS_MTF_VALUE = None
RLN_SAMPLING_IS_3D = None
RLN_SAMPLING_IS_3D_TRANS = None
RLN_SAMPLING_HEALPIX_ORDER = None
RLN_SAMPLING_LIMIT_TILT = None
RLN_SAMPLING_OFFSET_RANGE = None
RLN_SAMPLING_OFFSET_STEP = None
RLN_SAMPLING_PERTURB = None
RLN_SAMPLING_PERTURBATION_FACTOR = None
RLN_SAMPLING_PRIOR_MODE = None
RLN_SAMPLING_PSI_STEP = None
RLN_SAMPLING_SIGMA_ROT = None
RLN_SAMPLING_SIGMA_TILT = None
RLN_SAMPLING_SIGMA_PSI = None
RLN_SAMPLING_SYMMETRY = None

RLN_SELECTED = None
RLN_SELECT_PARTICLES_ZSCORE = None
RLN_SORTED_IDX = None
RLN_PERFRAME_CUMULATIVE_WEIGHT = None
RLN_PERFRAME_RELATIVE_WEIGHT = None

RLN_RESOLUTION = None
RLN_RESOLUTION_ANGSTROM = None
RLN_RESOLUTION_INVPIXEL = None
RLN_SPECTRAL_IDX = None

# new labels in Relion 2.1
RLN_MLMODEL_ESTIM_RESOL_REF = None
RLN_MLMODEL_FOURIER_COVERAGE_REF = None
RLN_MLMODEL_FOURIER_COVERAGE_TOTAL_REF = None
RLN_OPTIMISER_LOCAL_SYMMETRY_FILENAME = None

# SGD labels in Relion 2.1
RLN_MLMODEL_SGD_GRADIENT_IMAGE = None
RLN_OPTIMISER_DO_SGD = None
RLN_OPTIMISER_SGD_MU = None
RLN_OPTIMISER_SGD_SIGMA2FUDGE_INI = None
RLN_OPTIMISER_SGD_SIGMA2FUDGE_HALFLIFE = None
RLN_OPTIMISER_SGD_SUBSET_START = None
RLN_OPTIMISER_SGD_SUBSET_SIZE = None
RLN_OPTIMISER_SGD_WRITE_EVERY_SUBSET = None
RLN_OPTIMISER_SGD_MAX_SUBSETS = None
RLN_OPTIMISER_SGD_STEPSIZE = None
RLN_OPTIMISER_HIGHRES_LIMIT_SGD = None

# ---- BSOFT labels
BSOFT_ID = None
BSOFT_PROJECT = None
BSOFT_FIELD = None
BSOFT_FIELD_ID = None
BSOFT_MAP = None
BSOFT_MAP_ID = None
BSOFT_MAP_REFERENCE = None
BSOFT_MAP_RECONSTRUCTION = None
BSOFT_MAP_TRANSFORM_FILE = None
BSOFT_MAP_POWERSPEC_FILE = None
BSOFT_MAP_SIZE_X = None
BSOFT_MAP_SIZE_Y = None
BSOFT_MAP_SIZE_Z = None
BSOFT_MAP_ORIGIN_X = None
BSOFT_MAP_ORIGIN_Y = None
BSOFT_MAP_ORIGIN_Z = None
BSOFT_MAP_SCALE_X = None
BSOFT_MAP_SCALE_Y = None
BSOFT_MAP_SCALE_Z = None
BSOFT_MAP_VOXEL_SIZE = None
BSOFT_MAP_SELECT = None
BSOFT_MAP_FOM = None
BSOFT_MAP_MAGNIFICATION = None
BSOFT_MAP_VIEW_X = None
BSOFT_MAP_VIEW_Y = None
BSOFT_MAP_VIEW_Z = None
BSOFT_MAP_VIEW_ANGLE = None
BSOFT_MAP_BACK_RWEIGHT = None
BSOFT_MAP_MODEL = None
BSOFT_MAP_SYMMETRY = None
BSOFT_MICROGRAPH_FILE = None
BSOFT_MICROGRAPH_PARTICLE_FILE = None
BSOFT_MICROGRAPH_FILAMENT_FILE = None
BSOFT_MICROGRAPH_TRANSFORM_FILE = None
BSOFT_MICROGRAPH_POWERSPEC_FILE = None
BSOFT_MICROGRAPH_ID = None
BSOFT_MICROGRAPH_FIELD_ID = None
BSOFT_MICROGRAPH_NUMBER = None
BSOFT_MICROGRAPH_SELECT = None
BSOFT_MICROGRAPH_FOM = None
BSOFT_MICROGRAPH_MAGNIFICATION = None
BSOFT_MICROGRAPH_SAMPLING = None
BSOFT_MICROGRAPH_PIXEL = None
BSOFT_MICROGRAPH_UNITS = None
BSOFT_MICROGRAPH_DOSE = None
BSOFT_MICROGRAPH_ORIGIN_X = None
BSOFT_MICROGRAPH_ORIGIN_Y = None
BSOFT_MICROGRAPH_ORIGIN_Z = None
BSOFT_MICROGRAPH_SCALE_X = None
BSOFT_MICROGRAPH_SCALE_Y = None
BSOFT_MICROGRAPH_SCALE_Z = None
BSOFT_MICROGRAPH_TILT_AXIS = None
BSOFT_MICROGRAPH_TILT_ANGLE = None
BSOFT_MICROGRAPH_LEVEL_ANGLE = None
BSOFT_MICROGRAPH_ROT_ANGLE = None
BSOFT_MICROGRAPH_VIEW_X = None
BSOFT_MICROGRAPH_VIEW_Y = None
BSOFT_MICROGRAPH_VIEW_Z = None
BSOFT_MICROGRAPH_VIEW_ANGLE = None
BSOFT_MICROGRAPH_MATRIX_1_1 = None
BSOFT_MICROGRAPH_MATRIX_1_2 = None
BSOFT_MICROGRAPH_MATRIX_1_3 = None
BSOFT_MICROGRAPH_MATRIX_2_1 = None
BSOFT_MICROGRAPH_MATRIX_2_2 = None
BSOFT_MICROGRAPH_MATRIX_2_3 = None
BSOFT_MICROGRAPH_MATRIX_3_1 = None
BSOFT_MICROGRAPH_MATRIX_3_2 = None
BSOFT_MICROGRAPH_MATRIX_3_3 = None
BSOFT_MICROGRAPH_HVEC_X = None
BSOFT_MICROGRAPH_HVEC_Y = None
BSOFT_MICROGRAPH_HVEC_Z = None
BSOFT_MICROGRAPH_KVEC_X = None
BSOFT_MICROGRAPH_KVEC_Y = None
BSOFT_MICROGRAPH_KVEC_Z = None
BSOFT_MICROGRAPH_LVEC_X = None
BSOFT_MICROGRAPH_LVEC_Y = None
BSOFT_MICROGRAPH_LVEC_Z = None
BSOFT_MICROGRAPH_HELIX_AXIS = None
BSOFT_MICROGRAPH_HELIX_RISE = None
BSOFT_MICROGRAPH_HELIX_ANGLE = None
BSOFT_MICROGRAPH_HELIX_RADIUS = None
BSOFT_MICROGRAPH_VOLTAGE = None
BSOFT_MICROGRAPH_CTF_CS = None
BSOFT_MICROGRAPH_CTF_CC = None
BSOFT_MICROGRAPH_CTF_ALPHA = None
BSOFT_MICROGRAPH_CTF_DE = None
BSOFT_MICROGRAPH_CTF_AMP_CONT = None
BSOFT_MICROGRAPH_CTF_ZERO = None
BSOFT_MICROGRAPH_CTF_DEF_AVG = None
BSOFT_MICROGRAPH_CTF_DEF_DEV = None
BSOFT_MICROGRAPH_CTF_DEF_MIN = None
BSOFT_MICROGRAPH_CTF_DEF_MAX = None
BSOFT_MICROGRAPH_CTF_AST_ANG = None
BSOFT_MICROGRAPH_CTF_BASELINE = None
BSOFT_MICROGRAPH_CTF_ENVELOPE = None
BSOFT_MICROGRAPH_BOX_RADIUS = None
BSOFT_MICROGRAPH_BOX_RADIUS_X = None
BSOFT_MICROGRAPH_BOX_RADIUS_Y = None
BSOFT_MICROGRAPH_BOX_RADIUS_Z = None
BSOFT_MICROGRAPH_BAD = None
BSOFT_MICROGRAPH_BAD_RADIUS = None
BSOFT_MICROGRAPH_BAD_X = None
BSOFT_MICROGRAPH_BAD_Y = None
BSOFT_MICROGRAPH_BAD_Z = None
BSOFT_MICROGRAPH_MARKER_RADIUS = None
BSOFT_MICROGRAPH_MARKER_ID = None
BSOFT_MICROGRAPH_MARKER_X = None
BSOFT_MICROGRAPH_MARKER_Y = None
BSOFT_MICROGRAPH_MARKER_Z = None
BSOFT_MICROGRAPH_MARKER_ERROR_X = None
BSOFT_MICROGRAPH_MARKER_ERROR_Y = None
BSOFT_MICROGRAPH_MARKER_ERROR_Z = None
BSOFT_MICROGRAPH_MARKER_FOM = None
BSOFT_MICROGRAPH_FILAMENT_WIDTH = None
BSOFT_MICROGRAPH_FILNODE_RADIUS = None
BSOFT_CTF = None
BSOFT_CTF_VOLTAGE = None
BSOFT_CTF_CS = None
BSOFT_CTF_CC = None
BSOFT_CTF_ALPHA = None
BSOFT_CTF_DE = None
BSOFT_CTF_AMP = None
BSOFT_CTF_ZERO = None
BSOFT_CTF_DEF_AVG = None
BSOFT_CTF_DEF_DEV = None
BSOFT_CTF_DEF_MIN = None
BSOFT_CTF_DEF_MAX = None
BSOFT_CTF_AST_ANG = None
BSOFT_CTF_BASELINE = None
BSOFT_CTF_ENVELOPE = None
BSOFT_PARTICLE = None
BSOFT_PARTICLE_FILE = None
BSOFT_PARTICLE_NUMBER = None
BSOFT_PARTICLE_ID = None
BSOFT_PARTICLE_GROUP = None
BSOFT_PARTICLE_MG_ID = None
BSOFT_PARTICLE_MG_X = None
BSOFT_PARTICLE_MG_Y = None
BSOFT_PARTICLE_MG_Z = None
BSOFT_PARTICLE_X = None
BSOFT_PARTICLE_Y = None
BSOFT_PARTICLE_Z = None
BSOFT_PARTICLE_X_ORIGIN = None
BSOFT_PARTICLE_Y_ORIGIN = None
BSOFT_PARTICLE_Z_ORIGIN = None
BSOFT_PARTICLE_ORIGIN_X = None
BSOFT_PARTICLE_ORIGIN_Y = None
BSOFT_PARTICLE_ORIGIN_Z = None
BSOFT_PARTICLE_PSI = None
BSOFT_PARTICLE_THETA = None
BSOFT_PARTICLE_PHI = None
BSOFT_PARTICLE_OMEGA = None
BSOFT_PARTICLE_VIEW_X = None
BSOFT_PARTICLE_VIEW_Y = None
BSOFT_PARTICLE_VIEW_Z = None
BSOFT_PARTICLE_VIEW_ANGLE = None
BSOFT_PARTICLE_MAGNIF = None
BSOFT_PARTICLE_DEFOCUS = None
BSOFT_PARTICLE_DEF_DEV = None
BSOFT_PARTICLE_AST_ANG = None
BSOFT_PARTICLE_SELECT = None
BSOFT_PARTICLE_FOM = None
BSOFT_PARTICLE_FOM_CV = None
BSOFT_PARTICLE_FOM_AVG = None
BSOFT_PARTICLE_FOM_STD = None
BSOFT_PARTICLE_HANDA_FOM = None
BSOFT_PARTICLE_HANDB_FOM = None
BSOFT_PARTICLE_CC = None
BSOFT_PARTICLE_PFT_CC = None
BSOFT_PARTICLE_PRJ_CC = None
BSOFT_PARTICLE_CMP_CC = None
BSOFT_PARTICLE_RFACTORAB = None
BSOFT_PARTICLE_COVERAGE = None
BSOFT_PARTICLE_BOX_SIZE = None
BSOFT_PARTICLE_BOX_SIZE_X = None
BSOFT_PARTICLE_BOX_SIZE_Y = None
BSOFT_PARTICLE_BOX_SIZE_Z = None
BSOFT_PARTICLE_BOX_RADIUS = None
BSOFT_PARTICLE_BOX_RADIUS_X = None
BSOFT_PARTICLE_BOX_RADIUS_Y = None
BSOFT_PARTICLE_BOX_RADIUS_Z = None
BSOFT_PARTICLE_BAD = None
BSOFT_PARTICLE_BAD_RADIUS = None
BSOFT_PARTICLE_BAD_X = None
BSOFT_PARTICLE_BAD_Y = None
BSOFT_PARTICLE_BAD_Z = None
BSOFT_FILAMENT = None
BSOFT_FILAMENT_FILE = None
BSOFT_FILAMENT_ID = None
BSOFT_FILAMENT_NODE = None
BSOFT_FILAMENT_NODE_ID = None
BSOFT_FILAMENT_NODE_X = None
BSOFT_FILAMENT_NODE_Y = None
BSOFT_FILAMENT_NODE_Z = None
BSOFT_FILAMENT_WIDTH = None
BSOFT_FILNODE_RADIUS = None
BSOFT_ORIENT_ID = None
BSOFT_ORIENT_ORIGIN_X = None
BSOFT_ORIENT_ORIGIN_Y = None
BSOFT_ORIENT_ORIGIN_Z = None
BSOFT_ORIENT_VIEW_X = None
BSOFT_ORIENT_VIEW_Y = None
BSOFT_ORIENT_VIEW_Z = None
BSOFT_ORIENT_VIEW_ANGLE = None
BSOFT_ORIENT_FOM = None
BSOFT_ORIENT_SELECT = None
BSOFT_MARKER = None
BSOFT_MARKER_RADIUS = None
BSOFT_MARKER_ID = None
BSOFT_MARKER_X = None
BSOFT_MARKER_Y = None
BSOFT_MARKER_Z = None
BSOFT_MARKER_ERROR_X = None
BSOFT_MARKER_ERROR_Y = None
BSOFT_MARKER_ERROR_Z = None
BSOFT_MARKER_IMAGE = None
BSOFT_MARKER_RESIDUAL = None
BSOFT_MARKER_FOM = None
BSOFT_MARKER_SELECT = None
BSOFT_REFLEX = None
BSOFT_REFLEX_RADIUS = None
BSOFT_REFLEX_X = None
BSOFT_REFLEX_Y = None
BSOFT_REFLEX_Z = None
BSOFT_REFLEX_H = None
BSOFT_REFLEX_K = None
BSOFT_REFLEX_L = None
BSOFT_REFLEX_AMP = None
BSOFT_REFLEX_SIGAMP = None
BSOFT_REFLEX_PHI = None
BSOFT_REFLEX_SIGPHI = None
BSOFT_REFLEX_FOM = None
BSOFT_REFLEX_STATUS = None
BSOFT_LAYERLINE = None
BSOFT_LAYERLINE_NUMBER = None
BSOFT_LAYERLINE_ORDER = None
BSOFT_LAYERLINE_DISTANCE = None
BSOFT_LAYERLINE_FREQ = None
BSOFT_LAYERLINE_AMP = None
BSOFT_LAYERLINE_FOM = None
BSOFT_LAYERLINE_SELECT = None

BSOFT_SYMMETRY_INT_TABLES_NUMBER = None
BSOFT_SYMMETRY_SPACE_GROUP_NAME_H_M = None
BSOFT_SYMMETRY_CELL_SETTING = None
BSOFT_SYMMETRY_EQUIV_ID = None
BSOFT_SYMMETRY_EQUIV_POS_AS_XYZ = None


# Functions
def getBlocksInMetaDataFile():
    pass


def label2Str():
    pass


def colorStr():
    pass


def labelType():
    pass


def labelHasTag():
    pass


def labelIsImage():
    pass


def str2Label():
    pass


def isValidLabel():
    pass


def MDValueRelational():
    pass


def MDValueEQ():
    pass


def MDValueNE():
    pass


def MDValueLT():
    pass


def MDValueLE():
    pass


def MDValueGT():
    pass


def MDValueGE():
    pass


def MDValueRange():
    pass


def addLabelAlias():
    pass


def activateMathExtensions():
    pass


class SymList:
    def getSymmetryMatrices(self):
        pass


def MetaData():
    print(ghostStr)


MetaDataInfo = None

HEADER = None


class Image:
    def __init__(self):
        pass

    def read(self, *args, **kwargs):
        print("GHOST in place, read call ignored!.")

    def getDimensions(self):
        return None, None, None, None


def Euler_angles2matrix():
    pass


class FileName:
    """ Try to implement some basic code to reach further without xmipp"""
    imageExtentions = []

    def __init__(self, path):
        self.path = path

    def isImage(self):
        return True
