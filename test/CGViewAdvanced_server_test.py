# -*- coding: utf-8 -*-
import os
import sys
import time
import unittest
import shutil
from configparser import ConfigParser

from CGViewAdvanced.CGViewAdvancedImpl import CGViewAdvanced
from CGViewAdvanced.CGViewAdvancedServer import MethodContext
from CGViewAdvanced.authclient import KBaseAuth as _KBaseAuth
from CGViewAdvanced.Utils import CGViewUtil as cgu
from installed_clients.WorkspaceClient import Workspace
from installed_clients.GenomeFileUtilClient import GenomeFileUtil


class CGViewAdvancedTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('CGViewAdvanced'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'CGViewAdvanced',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = CGViewAdvanced(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        suffix = int(time.time() * 1000)
        cls.wsName = "test_ContigFilter_" + str(suffix)
        ret = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(cls):
        return cls.__class__.ws

    def getWsName(cls):
        if hasattr(cls.__class__, 'wsName'):
            return cls.__class__.wsName
        suffix = int(time.time() * 1000)
        wsName = "test_CGViewAdvanced_" + str(suffix)
        cls.__class__.wsName = wsName
        return wsName

    def get_genome_ref(cls):
        test_genome_path = os.path.join(cls.scratch, 'QGKT01000001.1.gb')
        shutil.copy('data/QGKT01000001.1.gb', test_genome_path)
        print("====dir", os.listdir("data"))
        gfu = GenomeFileUtil(cls.callback_url)
        genome_ref = gfu.genbank_to_genome({'workspace_name': cls.getWsName(),
                                            'genome_name': "test_genome",
                                            'file': {'path': test_genome_path}})
        return genome_ref['genome_ref']

    def get_testing_params(cls, default=True):
        genome_ref = cls.get_genome_ref()
        if default:
            ret = {'input_file': genome_ref,
                              'linear': 0,
                              'gc_content': 1,
                              'gc_skew': 1,
                              'at_content': 0,
                              'at_skew': 0,
                              'average': 1,
                              'scale': 1,
                              'orfs': 0,
                              'combined_orfs': 0,
                              'orf_size': 100,
                              'tick_density': 0.5,
                              'details': 1,
                              'legend': 1,
                              'condensed': 0,
                              'feature_labels': 0,
                              'orf_labels': 0,
                              'show_sequence_features': 1
                              }
        else:
            ret = {'input_file': genome_ref,
                               'linear': 1,
                               'gc_content': 0,
                               'gc_skew': 0,
                               'at_content': 1,
                               'at_skew': 1,
                               'average': 0,
                               'scale': 0,
                               'orfs': 1,
                               'combined_orfs': 1,
                               'orf_size': 200,
                               'tick_density': 0.7,
                               'details': 0,
                               'legend': 0,
                               'condensed': 1,
                               'feature_labels': 1,
                               'orf_labels': 1,
                               'show_sequence_features': 0
                               }
        return ret

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_command_to_execute(cls):
        params_default = cls.get_testing_params()
        params_opposite = cls.get_testing_params(False)
        cmd_default = cgu.build_cgview_xml_cmd(params_default)
        cmd_opposite = cgu.build_cgview_xml_cmd(params_opposite)
        cls.assertEqual(cmd_default, ['-linear', 'F'])
        cls.assertEqual(cmd_opposite, ['-linear', 'T', '-gc_content', 'F', '-gc_skew', 'F', '-at_content', 'T', '-at_skew', 'T', '-average', 'F', '-scale', 'F', '-orfs', 'T', '-combined_orfs', 'T', '-orf_size', '200', '-tick_density', '0.7', '-details', 'F', '-legend', 'F', '-condensed', 'T', '-feature_labels', 'T', '-orf_labels', 'T', '-show_sequence_features', 'F'])


    def test_all_files_generated(self):
        # Prepare test objects in workspace if needed using
        # self.getWsClient().save_objects({'workspace': self.getWsName(),
        #                                  'objects': []})
        #
        # Run your method by
        # ret = self.getImpl().your_method(self.getContext(), parameters...)
        #
        # Check returned data with
        # self.assertEqual(ret[...], ...) or other unittest methods
        genome_ref = self.get_genome_ref()
        ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
                                                             'input_file': genome_ref,
                                                             'linear': 0,
                                                             'gc_content': 1,
                                                             'gc_skew': 1,
                                                             'at_content': 0,
                                                             'at_skew': 0,
                                                             'average': 1,
                                                             'scale': 1,
                                                             'orfs':0,
                                                             'combined_orfs':0,
                                                             'orf_size': 100,
                                                             'tick_density': 0.5,
                                                             'details': 1,
                                                             'legend': 1,
                                                             'condensed': 0,
                                                             'feature_labels': 0,
                                                             'orf_labels': 0,
                                                             'show_sequence_features': 1
                                                             })
        # Create file paths
        output_dir = os.path.join(self.scratch, 'output_folder')
        image_output_dir = os.path.join(output_dir, 'image_outputs')
        xml_output_dir = os.path.join(output_dir, 'xml_outputs')

        # xml file generated
        has_xml = os.path.join(xml_output_dir, 'KBase_derived_test_genome.xml')
        self.assertTrue(has_xml)

        # # all image files generated
        has_png = os.path.join(image_output_dir, 'KBase_derived_test_genome.png')
        has_jpg = os.path.join(image_output_dir, 'KBase_derived_test_genome.jpg')
        has_svg = os.path.join(image_output_dir, 'KBase_derived_test_genome.svg')
        self.assertTrue(has_png)
        self.assertTrue(has_jpg)
        self.assertTrue(has_svg)


    # def test_linear(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'linear': 1,
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':0,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_gccontent(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'linear': 0,
    #                                                          'gc_content': 0,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':0,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_gcskew(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'linear': 0,
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 0,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':0,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_atcontent(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'input_file': '29796/9/1',
    #                                                          'linear': 0,
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 1,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':0,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_atskew(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'linear': 0,
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 1,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':0,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_average(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 0,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':0,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_scale(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 0,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':0,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_readingframes(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 1,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':0,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_orfs(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':1,
    #                                                          'combined_orfs':0,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1                                                             })
    # def test_combined_orfs(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':1,
    #                                                          'combined_orfs':1,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_orf_size(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':1,
    #                                                          'combined_orfs':1,
    #                                                          'orf_size': 150,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_condensed(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':1,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 1,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_featurelabels(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':1,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 1,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_orflabels(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':1,
    #                                                          'combined_orfs':1,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 0,
    #                                                          'orf_labels': 1,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_tick_density(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':1,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.6,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 1,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_details(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':1,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 0,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 1,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_legend(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':1,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 0,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 1,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_opacity(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':1,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 1,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 1,
    #                                                          'show_sequence_features': 1
    #                                                          })
    # def test_showseqfeatures(self):
    #     ret = self.serviceImpl.run_CGViewAdvanced(self.ctx, {'workspace_name': self.wsName,
    #                                                          'input_file': '29796/9/1',
    #                                                          'gc_content': 1,
    #                                                          'gc_skew': 1,
    #                                                          'at_content': 0,
    #                                                          'at_skew': 0,
    #                                                          'average': 1,
    #                                                          'scale': 1,
    #                                                          'reading_frames': 0,
    #                                                          'orfs':0,
    #                                                          'combined_orfs':1,
    #                                                          'orf_size': 100,
    #                                                          'tick_density': 0.5,
    #                                                          'details': 1,
    #                                                          'legend': 1,
    #                                                          'condensed': 0,
    #                                                          'feature_labels': 1,
    #                                                          'orf_labels': 0,
    #                                                          'use_opacity': 0,
    #                                                          'show_sequence_features': 0
    #                                                          })
