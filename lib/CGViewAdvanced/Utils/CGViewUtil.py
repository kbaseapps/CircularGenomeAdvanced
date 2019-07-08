import os
import ntpath
import subprocess
import shutil
from installed_clients.GenomeFileUtilClient import GenomeFileUtil

from installed_clients.KBaseReportClient import KBaseReport

# Validate mandatory keys and orfs
def process_params(params):
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

# Perform GenomeFileUtil operations and create Genbank file from KBase Genome object
def fetch_genome_files(self, params, gbk_dir):
    gfu = GenomeFileUtil(self.callback_url)
    gbk = gfu.genome_to_genbank({'genome_ref':params['input_file']})
    gbk_file = gbk["genbank_file"]["file_path"]
    base = ntpath.basename(gbk_file).rsplit(".", 1)[0]
    name_gbff =  base + ".gbff"
    name_gbk = base + ".gbk"
    shutil.copy(gbk_file, gbk_dir)
    gbff_path = os.path.join(gbk_dir, name_gbff)
    gbk_path = os.path.join(gbk_dir, name_gbk)
    shutil.move(gbff_path, gbk_path)
    return base, gbk_path

#build command for cgview_xml_builder
def build_cgview_xml_cmd(params):
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

# Build XML file from command list
def run_cmd_to_build_xml(cmd, xml_output_dir, base, gbk_path):
    os.chdir("/opt/cgview/cgview_xml_builder")
    xml_file = os.path.join(xml_output_dir, base+".xml")
    required_cmd = ["perl", "cgview_xml_builder.pl", "-sequence", gbk_path, "-output", xml_file, "-size", "small"]
    exec_cmd = required_cmd + cmd
    print("=====final cmd", exec_cmd)
    p = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    (stdout, stderr) = p.communicate()
    if p.returncode != 0:
        print(stderr)
    return xml_file

# Create images from XML file
def create_imgs_from_xml(image_output_dir, xml_file, base):
    os.chdir("/opt/cgview")
    png_file = os.path.join(image_output_dir, base+".png")
    jpg_file = os.path.join(image_output_dir, base+".jpg")
    svg_file = os.path.join(image_output_dir, base+".svg")
    png_path = os.path.join(png_file)
    jpg_path = os.path.join(jpg_file)
    svg_path = os.path.join(svg_file)
    # Create PNG
    png_cmd = ["java", "-jar", "cgview.jar", "-i", xml_file, "-o", png_file, "-f", "png", "-A", "12", "-D", "12", "-W", "800", "-H", "800"]
    p = subprocess.Popen(png_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    (stdout, stderr) = p.communicate()
    if p.returncode != 0:
        print(stderr)
    # Create JPG
    jpg_cmd = ["java", "-jar", "cgview.jar", "-i", xml_file, "-o", jpg_file, "-f", "jpg", "-A", "12", "-D", "12", "-W", "800", "-H", "800"]
    p = subprocess.Popen(jpg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    (stdout, stderr) = p.communicate()
    if p.returncode != 0:
        print(stderr)
    # Create SVG
    svg_cmd = ["java", "-jar", "cgview.jar", "-i", xml_file, "-o", svg_file, "-f", "svg", "-A", "12", "-D", "12", "-W", "800", "-H", "800"]
    p = subprocess.Popen(svg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    (stdout, stderr) = p.communicate()
    if p.returncode != 0:
        print(stderr)
    return png_path, jpg_path, svg_path

# Generate report
def gen_report(self, params, png_path, jpg_path, svg_path, base):
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