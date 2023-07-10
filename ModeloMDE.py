"""
Model exported as python.
Name : AreaAPPUR
Group : 
With QGIS : 32209
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsCoordinateReferenceSystem
import processing


class Areaappur(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('mosaico', 'Mosaico', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('rea', 'Area', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Declividade_final', 'Declividade_Final', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Uso_restrito_25_45_final', 'Uso_Restrito_25_45_Final', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Uso_restrito_45mais_final', 'Uso_Restrito_45mais_Final', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Nascentes_final', 'Nascentes_Final', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Drenagem_final', 'Drenagem_Final', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(16, model_feedback)
        results = {}
        outputs = {}

        # Reprojetar camada
        alg_params = {
            'INPUT': parameters['rea'],
            'OPERATION': '',
            'TARGET_CRS': 'ProjectCrs',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Reprojetar coordenadas
        alg_params = {
            'DATA_TYPE': 0,  # Use Camada de entrada Tipo Dado
            'EXTRA': '',
            'INPUT': parameters['mosaico'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,  # Vizinho mais próximo
            'SOURCE_CRS': None,
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCoordenadas'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Reprojetar coordenadas
        alg_params = {
            'DATA_TYPE': 0,  # Use Camada de entrada Tipo Dado
            'EXTRA': '',
            'INPUT': outputs['ReprojetarCoordenadas']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,  # Vizinho mais próximo
            'SOURCE_CRS': None,
            'TARGET_CRS': 'ProjectCrs',
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCoordenadas'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # r.fill.dir
        alg_params = {
            '-f': False,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'format': 0,  # grass
            'input': outputs['ReprojetarCoordenadas']['OUTPUT'],
            'areas': QgsProcessing.TEMPORARY_OUTPUT,
            'direction': QgsProcessing.TEMPORARY_OUTPUT,
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rfilldir'] = processing.run('grass7:r.fill.dir', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # r.stream.extract
        alg_params = {
            'GRASS_OUTPUT_TYPE_PARAMETER': 0,  # auto
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_EXPORT_NOCAT': False,
            'GRASS_VECTOR_LCO': '',
            'accumulation': None,
            'd8cut': None,
            'depression': None,
            'elevation': outputs['Rfilldir']['output'],
            'memory': 300,
            'mexp': 0,
            'stream_length': 50,
            'threshold': 30000,
            'stream_raster': QgsProcessing.TEMPORARY_OUTPUT,
            'stream_vector': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rstreamextract'] = processing.run('grass7:r.stream.extract', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Declividade
        alg_params = {
            'AS_PERCENT': False,
            'BAND': 1,
            'COMPUTE_EDGES': False,
            'EXTRA': '',
            'INPUT': outputs['ReprojetarCoordenadas']['OUTPUT'],
            'OPTIONS': '',
            'SCALE': 1,
            'ZEVENBERGEN': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Declividade'] = processing.run('gdal:slope', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Reclassificar por tabela
        alg_params = {
            'DATA_TYPE': 5,  # Float32
            'INPUT_RASTER': outputs['Declividade']['OUTPUT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 0,  # min < valor <= max
            'RASTER_BAND': 1,
            'TABLE': ['0','45','0','45','100','1'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReclassificarPorTabela'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Recortar raster pela camada de máscara
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use Camada de entrada Tipo Dado
            'EXTRA': '',
            'INPUT': outputs['ReclassificarPorTabela']['OUTPUT'],
            'KEEP_RESOLUTION': False,
            'MASK': outputs['ReprojetarCamada']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': 'ProjectCrs',
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': parameters['Uso_restrito_45mais_final']
        }
        outputs['RecortarRasterPelaCamadaDeMscara'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Uso_restrito_45mais_final'] = outputs['RecortarRasterPelaCamadaDeMscara']['OUTPUT']

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Recortar raster pela camada de máscara
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use Camada de entrada Tipo Dado
            'EXTRA': '',
            'INPUT': outputs['Declividade']['OUTPUT'],
            'KEEP_RESOLUTION': False,
            'MASK': outputs['ReprojetarCamada']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': 'ProjectCrs',
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': parameters['Declividade_final']
        }
        outputs['RecortarRasterPelaCamadaDeMscara'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Declividade_final'] = outputs['RecortarRasterPelaCamadaDeMscara']['OUTPUT']

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Reclassificar por tabela
        alg_params = {
            'DATA_TYPE': 5,  # Float32
            'INPUT_RASTER': outputs['Declividade']['OUTPUT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 0,  # min < valor <= max
            'RASTER_BAND': 1,
            'TABLE': ['0','25','0','25','45','1','45','100','0'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReclassificarPorTabela'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # r.to.vect
        alg_params = {
            '-b': False,
            '-s': False,
            '-t': False,
            '-v': False,
            '-z': False,
            'GRASS_OUTPUT_TYPE_PARAMETER': 0,  # auto
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_EXPORT_NOCAT': False,
            'GRASS_VECTOR_LCO': '',
            'column': 'value',
            'input': outputs['Rstreamextract']['stream_raster'],
            'type': 0,  # line
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rtovect'] = processing.run('grass7:r.to.vect', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Recortar raster pela camada de máscara
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use Camada de entrada Tipo Dado
            'EXTRA': '',
            'INPUT': outputs['ReclassificarPorTabela']['OUTPUT'],
            'KEEP_RESOLUTION': False,
            'MASK': outputs['ReprojetarCamada']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': 'ProjectCrs',
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': parameters['Uso_restrito_25_45_final']
        }
        outputs['RecortarRasterPelaCamadaDeMscara'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Uso_restrito_25_45_final'] = outputs['RecortarRasterPelaCamadaDeMscara']['OUTPUT']

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Selecionar por uma expressão
        alg_params = {
            'EXPRESSION': ' "type_code" = 0',
            'INPUT': outputs['Rstreamextract']['stream_vector'],
            'METHOD': 0,  # Criar uma nova seleção
        }
        outputs['SelecionarPorUmaExpresso'] = processing.run('qgis:selectbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Recortar
        alg_params = {
            'INPUT': outputs['Rtovect']['output'],
            'OVERLAY': outputs['ReprojetarCamada']['OUTPUT'],
            'OUTPUT': parameters['Drenagem_final']
        }
        outputs['Recortar'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Drenagem_final'] = outputs['Recortar']['OUTPUT']

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Salvar feições vetoriais em arquivo
        alg_params = {
            'DATASOURCE_OPTIONS': '',
            'INPUT': outputs['SelecionarPorUmaExpresso']['OUTPUT'],
            'LAYER_NAME': 'Nascentes',
            'LAYER_OPTIONS': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SalvarFeiesVetoriaisEmArquivo'] = processing.run('native:savefeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Recortar
        alg_params = {
            'INPUT': outputs['SalvarFeiesVetoriaisEmArquivo']['OUTPUT'],
            'OVERLAY': outputs['ReprojetarCamada']['OUTPUT'],
            'OUTPUT': parameters['Nascentes_final']
        }
        outputs['Recortar'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Nascentes_final'] = outputs['Recortar']['OUTPUT']
        return results

    def name(self):
        return 'AreaAPPUR'

    def displayName(self):
        return 'AreaAPPUR'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Areaappur()
