# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import subprocess
from installed_clients.GenomeFileUtilClient import GenomeFileUtil

from installed_clients.KBaseReportClient import KBaseReport
#END_HEADER


class CGViewAdvanced:
    '''
    Module Name:
    CGViewAdvanced

    Module Description:
    A KBase module: CGViewAdvanced
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def run_CGViewAdvanced(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_CGViewAdvanced
        if 'workspace_name' not in params:
            raise ValueError('Parameter workspace_name is not set in input arguments')
        workspace_name = params['workspace_name']
        if 'input_file' not in params:
            raise ValueError('Parameter input_file is not set in input arguments')
        input_file = params['input_file']

        # Turn genome object to Genbank file
        gfu = GenomeFileUtil(self.callback_url)
        gbk = gfu.genome_to_genbank({'genome_ref':input_file})
        gbk_file = gbk["genbank_file"]["file_path"]

        #Make output directory
        output_dir= os.path.join(self.shared_folder, 'output_folder')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        #Test call
        os.chdir("/opt/cgview")
        test_output_file_path = os.path.join(output_dir, "cybercell.png")
        subprocess.call(["java", "-jar", "cgview.jar", "-i", "cybercell.xml", "-o", test_output_file_path, "-f", "png"])
        print("==== output png correctly", os.listdir(output_dir) )
        png_path = os.path.join(test_output_file_path)
        png_dict = {"path":png_path, 'name': 'Circular_Genome_Map_PNG'}
        # html_path = "/"
        html_dict = {'path':png_path,'name':'Circular Genome Map'}
        report_client = KBaseReport(self.callback_url)
        report_info = report_client.create_extended_report({
            'direct_html_link_index': 0,
            'html_links':[html_dict],
            'file_links':[png_dict],
            'workspace_name': params['workspace_name']
        })
        output = {
            'report_name': report_info['name'],
            'report_ref': report_info['ref'],
        }
        #END run_CGViewAdvanced

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_CGViewAdvanced return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
