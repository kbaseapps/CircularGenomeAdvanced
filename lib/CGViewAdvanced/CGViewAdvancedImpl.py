# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import ntpath
import subprocess
import fpdf
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
    GIT_URL = "https://github.com/kellyhuang21/CircularGenomeAdvanced.git"
    GIT_COMMIT_HASH = "4beb228f8fd231e6fcb2ec846d3cf1fe0c87518e"

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

    # Validate mandatory keys and orfs
    def process_params(self, params):
        if 'workspace_name' not in params:
            raise ValueError('Parameter workspace_name is not set in input arguments')
        if 'input_file' not in params:
            raise ValueError('Parameter input_file is not set in input arguments')
        # Raise orfs errors
        orfs = params['orfs']
        if params['combined_orfs']==1 and orfs == 0:
            raise ValueError("'Orfs' parameter must be selected to use 'Combined Orfs'")
        if params['orf_size']==1 and orfs == 0:
            raise ValueError("'Orfs' parameter must be selected to use 'Orf Size'")
        if params['orf_labels']==1 and orfs == 0:
            raise ValueError("'Orfs' parameter must be selected to use 'Orf Labels'")

    # Perform GenomeFileUtil operations
    def fetch_genome_files(self, params, gbk_dir):
        # Turn genome object to Genbank file
        gfu = GenomeFileUtil(self.callback_url)
        gbk = gfu.genome_to_genbank({'genome_ref':params['input_file']})
        gbk_file = gbk["genbank_file"]["file_path"]
        base = ntpath.basename(gbk_file).rsplit(".", 1)[0]
        name_gbff =  base + ".gbff"
        name_gbk = base + ".gbk"
        subprocess.call(["cp", gbk_file, gbk_dir])
        gbff_path = os.path.join(gbk_dir, name_gbff)
        gbk_path = os.path.join(gbk_dir, name_gbk)
        subprocess.call(["mv", gbff_path, gbk_path])
        return base, gbk_path

    #build command for cgview_xml_builder
    def build_cgview_xml_cmd(self, params):
        # Create list of parameters to call
        cmd = []
        # if len(title) != 0:
        #     cmd.extend(["-title", '"' + str(title) + '"'])
        if params['linear'] == 1:
            cmd.extend(["-linear", "T"])
        if params['linear'] == 0:
            cmd.extend(["-linear", "F"])
        if params['gc_content'] == 0:
            cmd.extend(["-gc_content", "F"])
        if params['gc_skew'] == 0:
            cmd.extend(["-gc_skew", "F"])
        if params['at_content'] == 1:
            cmd.extend(["-at_content", "T"])
        if params['at_skew'] == 1:
            cmd.extend(["-at_skew", "T"])
        if params['average'] == 0:
            cmd.extend(["-average", "F"])
        if params['scale'] == 0:
            cmd.extend(["-scale", "F"])
        # if reading_frames == 1:
        #     cmd.extend(["-reading_frames", "T"])
        if params['orfs'] == 1:
            cmd.extend(["-orfs", "T"])
        if params['combined_orfs'] == 1:
            cmd.extend(["-combined_orfs", "T"])
        if int(params['orf_size']) != 100:
            cmd.extend(["-orf_size", str(params['orf_size'])])
        if params['tick_density'] != 0.5:
            cmd.extend(["-tick_density", str(params['tick_density'])])
        if params['details'] == 0:
            cmd.extend(["-details", "F"])
        if params['legend'] == 0:
            cmd.extend(["-legend", "F"])
        if params['condensed'] == 1:
            cmd.extend(["-condensed", "T"])
        if params['feature_labels'] == 1:
            cmd.extend(["-feature_labels", "T"])
        if params['orf_labels'] == 1:
            cmd.extend(["-orf_labels", "T"])
        if params['show_sequence_features'] == 0:
            cmd.extend(["-show_sequence_features", "F"])
        return cmd

    def run_cmd_to_build_xml(self, cmd, xml_output_dir, base, gbk_path):
        # Build XML file from Genbank
        os.chdir("/opt/cgview/cgview_xml_builder")
        xml_file = os.path.join(xml_output_dir, base+".xml")
        required_cmd = ["perl", "cgview_xml_builder.pl", "-sequence", gbk_path, "-output", xml_file, "-size", "small"]
        exec_cmd = required_cmd + cmd
        print("=====final cmd", exec_cmd)
        subprocess.call(exec_cmd)
        return xml_file

    def create_imgs_from_xml(self, image_output_dir, xml_file, base):
        # Create image from XML
        os.chdir("/opt/cgview")
        png_file = os.path.join(image_output_dir, base+".png")
        jpg_file = os.path.join(image_output_dir, base+".jpg")
        svg_file = os.path.join(image_output_dir, base+".svg")
        png_path = os.path.join(png_file)
        jpg_path = os.path.join(jpg_file)
        svg_path = os.path.join(svg_file)
        subprocess.call(["java", "-jar", "cgview.jar", "-i", xml_file, "-o", png_file, "-f", "png", "-A", "12", "-D", "12", "-W", "800", "-H", "800"])
        subprocess.call(["java", "-jar", "cgview.jar", "-i", xml_file, "-o", jpg_file, "-f", "jpg", "-A", "12", "-D", "12", "-W", "800", "-H", "800"])
        subprocess.call(["java", "-jar", "cgview.jar", "-i", xml_file, "-o", svg_file, "-f", "svg", "-A", "12", "-D", "12", "-W", "800", "-H", "800"])
        return png_path, jpg_path, svg_path

    def gen_report(self, params, png_path, jpg_path, svg_path, base):
        # Create Report
        png_dict = {"path":png_path, 'name': base+'.png'}
        jpg_dict = {"path":jpg_path, 'name': base+'.jpg'}
        svg_dict = {"path":svg_path, 'name': base+'.svg'}

        html_dict = {'path':png_path,'name':base+' Map'}
        report_client = KBaseReport(self.callback_url)
        report_info = report_client.create_extended_report({
            'direct_html_link_index': 0,
            'html_links':[html_dict],
            'file_links':[png_dict, jpg_dict, svg_dict],
            'workspace_name': params['workspace_name'],
            'html_window_height':800,
            'summary_window_height':800
        })
        return report_info

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
        self.process_params(params)

        # Make output directory and subdirectories
        output_dir= os.path.join(self.shared_folder, 'output_folder')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        xml_output_dir= os.path.join(output_dir, 'xml_outputs')
        if not os.path.exists(xml_output_dir):
            os.makedirs(xml_output_dir)
        image_output_dir= os.path.join(output_dir, 'image_outputs')
        if not os.path.exists(image_output_dir):
            os.makedirs(image_output_dir)
        gbk_dir= os.path.join(output_dir, 'gbk_files')
        if not os.path.exists(gbk_dir):
            os.makedirs(gbk_dir)

        base, gbk_path = self.fetch_genome_files(params, gbk_dir)

        cmd = self.build_cgview_xml_cmd(params)

        xml_file = self.run_cmd_to_build_xml(cmd, xml_output_dir, base, gbk_path)

        png_path, jpg_path, svg_path = self.create_imgs_from_xml(image_output_dir, xml_file, base)

        report_info = self.gen_report(params, png_path, jpg_path, svg_path, base)

        # Test example output - works
        # os.chdir("/opt/cgview")
        # test_output_file_path = os.path.join(output_dir, "cybercell.png")
        # subprocess.call(["java", "-jar", "cgview.jar", "-i", "cybercell.xml", "-o", test_output_file_path, "-f", "png"])

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
