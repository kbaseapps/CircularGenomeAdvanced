# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import ntpath
import subprocess
from fpdf import FPDF
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

        # Setting all input parameters
        print("=====params", params)
        input_file = params['input_file']
        linear = params['linear']
        gc_content = params['gc_content']
        gc_skew = params['gc_skew']
        at_content = params['at_content']
        at_skew = params['at_skew']
        average = params['average']
        scale = params['scale']
        reading_frames = params['reading_frames']
        orfs = params['orfs']
        combined_orfs = params['combined_orfs']
        orf_size = params['orf_size']
        tick_density = params['tick_density']
        details = params['details']
        legend = params['legend']
        condensed = params['condensed']
        feature_labels = params['feature_labels']
        orf_labels = params['orf_labels']
        use_opacity = params['use_opacity']
        show_sequence_features = params['show_sequence_features']

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


        # Turn genome object to Genbank file
        gfu = GenomeFileUtil(self.callback_url)
        gbk = gfu.genome_to_genbank({'genome_ref':input_file})
        gbk_file = gbk["genbank_file"]["file_path"]
        base = ntpath.basename(gbk_file).rsplit(".", 1)[0]
        name_gbff =  base + ".gbff"
        name_gbk = base + ".gbk"
        subprocess.call(["cp", gbk_file, gbk_dir])
        gbff_path = os.path.join(gbk_dir, name_gbff)
        print("===== from", gbff_path)
        gbk_path = os.path.join(gbk_dir, name_gbk)
        print("===== to", gbk_path)
        subprocess.call(["mv", gbff_path, gbk_path])

        # Create list of parameters to call
        cmd = []
        if linear == 1:
            cmd.extend(["-linear", "T"])
        else:
            cmd.extend(["-linear", "F"])
        if gc_content == 0:
            cmd.extend(["-gc_content", "F"])
        if gc_skew == 1:
            cmd.extend(["-gc_skew", "T"])
        if at_content == 1:
            cmd.extend(["-at_content", "T"])
        if at_skew == 1:
            cmd.extend(["-at_skew", "T"])
        if average == 0:
            cmd.extend(["-average", "F"])
        if scale == 0:
            cmd.extend(["-scale", "F"])
        if reading_frames == 1:
            cmd.extend(["-reading_frames", "T"])
        if orfs == 1:
            cmd.extend(["-orfs", "T"])
        if combined_orfs == 1:
            cmd.extend(["-combined_orfs", "T"])
        if int(orf_size) != 100:
            cmd.extend(["-orf_size", str(orf_size)])
        if tick_density != 0.5:
            cmd.extend(["-tick_density", str(tick_density)])
        if details == 0:
            cmd.extend(["-details", "F"])
        if legend == 0:
            cmd.extend(["-legend", "F"])
        if condensed == 1:
            cmd.extend(["-condensed", "T"])
        if feature_labels == 1:
            cmd.extend(["-feature_labels", "T"])
        if orf_labels == 1:
            cmd.extend(["-orf_labels", "T"])
        if use_opacity == 1:
            cmd.extend(["-use_opacity", "T"])
        if show_sequence_features == 0:
            cmd.extend(["-show_sequence_features", "F"])
        print("====set cmd", cmd)

        # Build XML file from Genbank
        os.chdir("/opt/cgview/cgview_xml_builder")
        xml_file = os.path.join(xml_output_dir, base+".xml")
        print("=====", os.listdir("/opt/cgview/cgview_xml_builder"))
        print("===== path to gbk", gbk_path)
        required_cmd = ["perl", "cgview_xml_builder.pl", "-sequence", gbk_path, "-output", xml_file, "-size", "small"]
        exec_cmd = required_cmd + cmd
        print("=====final cmd", exec_cmd)
        subprocess.call(exec_cmd)
        print("=====xml output dir", os.listdir(xml_output_dir))

        # Create image from XML
        os.chdir("/opt/cgview")
        png_file = os.path.join(image_output_dir, base+".png")
        jpg_file = os.path.join(image_output_dir, base+".jpg")
        svg_file = os.path.join(image_output_dir, base+".svg")
        pdf_file = os.path.join(image_output_dir, base+".pdf")

        subprocess.call(["java", "-jar", "cgview.jar", "-i", xml_file, "-o", png_file, "-f", "png", "-A", "12", "-D", "12", "-W", "800", "-H", "800"])
        subprocess.call(["java", "-jar", "cgview.jar", "-i", xml_file, "-o", jpg_file, "-f", "jpg", "-A", "12", "-D", "12", "-W", "800", "-H", "800"])
        subprocess.call(["java", "-jar", "cgview.jar", "-i", xml_file, "-o", svg_file, "-f", "svg", "-A", "12", "-D", "12", "-W", "800", "-H", "800"])

        print("=====image output dir", os.listdir(image_output_dir))

        # Create pdf output
        pdf = FPDF()
        image = jpg_file
        pdf.add_page()
        pdf.image(image, 0, 0, 800, 800)
        pdf.output(pdf_file, "F")

        # Test example output - works
        # os.chdir("/opt/cgview")
        # test_output_file_path = os.path.join(output_dir, "cybercell.png")
        # subprocess.call(["java", "-jar", "cgview.jar", "-i", "cybercell.xml", "-o", test_output_file_path, "-f", "png"])
        print("==== output png correctly", os.listdir(output_dir))

        # Create Report
        png_path = os.path.join(png_file)
        jpg_path = os.path.join(jpg_file)
        svg_path = os.path.join(svg_file)
        pdf_path = os.path.join(pdf_file)
        png_dict = {"path":png_path, 'name': base+'_PNG'}
        jpg_dict = {"path":jpg_path, 'name': base+'_JPG'}
        svg_dict = {"path":svg_path, 'name': base+'_SVG'}
        pdf_dict = {"path":pdf_path, 'name': base+'_PDF'}

        html_dict = {'path':png_path,'name':base+'Circular Genome Map'}
        report_client = KBaseReport(self.callback_url)
        report_info = report_client.create_extended_report({
            'direct_html_link_index': 0,
            'html_links':[html_dict],
            'file_links':[png_dict, jpg_dict, svg_dict, pdf_dict],
            'workspace_name': params['workspace_name'],
            'html_window_height':800,
            'summary_window_height':800
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
