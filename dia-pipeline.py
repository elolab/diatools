#! /usr/bin/env python3

import sys
import os
import subprocess
import shutil
import argparse
import datetime
import string
import sys
import time
import traceback
import types
import tempfile
import shlex
import xml.etree.ElementTree as ET

class NonZeroReturnValueException(Exception):
    def __init__(self, returnvalue, msg):
        self.msg = msg
        self.returnvalue = returnvalue
        return

def  logline(text):
    log_fh.write(text+"\n")
    log_fh.flush()
    return


def decoyDB(db_fasta_fh):

    db_name = None
    with open("DB_with_decoys.fasta", "w") as decoy_ref_fh:
        cmd = [
               "/opt/OpenMS/bin/DecoyDatabase",
               "-in", db_fasta_fh.name,
               "-out", decoy_ref_fh.name,
               ]
        logline("Running pipeline command: "+" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=log_fh, stderr=log_fh)
        proc.wait()
        log_fh.flush()
        if proc.returncode != 0:
            raise NonZeroReturnValueException(proc.returncode, 'DecoyDatabase')
        db_name = decoy_ref_fh.name
    return db_name

def runMSGFPlus(DDA_DB_filename, DDA_filenames, threads):

    DDA_pep_xmls = []
    
    for DDA_filename in DDA_filenames:
        
        basename = os.path.basename(DDA_filename)
        
        if os.path.exists(os.path.splitext(basename)[0]+".pepXML"):
            print (os.path.split(basename)[0]+".pepXML exists, skipping MSGF+")
            DDA_pep_xmls.append(os.path.splitext(basename)[0]+".pepXML")
            
        else:
            
            msgf_cmd = [
                "java",
                "-Xmx120g",
                "-jar", "/opt/msgfplus/MSGFPlus.jar",
                "-d", DDA_DB_filename,
                "-s", DDA_filename,
                "-t", "10ppm",
                "-thread", threads,
                "-m", "3",
                "-tda", "0",
                "-o", os.path.splitext(basename)[0]+".mzid"
                ]

            
            logline("Running pipeline command: "+" ".join(msgf_cmd))
            msgf_proc = subprocess.Popen(msgf_cmd, stdout=log_fh, stderr=log_fh)
            msgf_proc.wait()
            log_fh.flush()
            if msgf_proc.returncode != 0:
                raise NonZeroReturnValueException(msgf_proc.returncode, 'MSGF+')

            idconvert_cmd = [
                "/opt/tpp/bin/idconvert", os.path.splitext(basename)[0]+".mzid",
                "--pepXML"
            ]

            logline("Running pipeline command: "+" ".join(idconvert_cmd))
            idconvert_proc = subprocess.Popen(idconvert_cmd, stdout=log_fh, stderr=log_fh)
            idconvert_proc.wait()
            log_fh.flush()
            if idconvert_proc.returncode != 0:
                raise NonZeroReturnValueException(idconvert_proc.returncode, 'idconvert')

            DDA_pep_xmls.append(os.path.splitext(basename)[0]+".pepXML")
           
    if os.path.exists("interact_msgf_pep.xml"):
        print ("interact_msgf_pep.xml file already exist, skipping merging comet files.")        
    else:
        xinteract_cmd = [
            "/opt/tpp/bin/xinteract",
            "-OARPd",
            "-dDECOY_",
            "-Ninteract_msgf_pep.xml",
            ]
        xinteract_cmd.extend(DDA_pep_xmls)
        logline("Running pipeline command: "+" ".join(xinteract_cmd))
        xinteract_proc = subprocess.Popen(xinteract_cmd, stdout=log_fh, stderr=log_fh)
        xinteract_proc.wait()
        log_fh.flush()
        if xinteract_proc.returncode != 0:
            raise NonZeroReturnValueException(xinteract_proc.returncode, 'xinteract')
       
    return
   
        
def runComet(comet_cfg_templateFile, DDA_DB_filename, DDA_filenames):

    DDA_basenames = []
    DDA_pep_xmls = []
    for DDA_filename in DDA_filenames:
        basename = os.path.basename(DDA_filename)
        if not os.path.islink(basename):
            os.symlink(DDA_filename, basename)
        DDA_basenames.append(basename)
        DDA_pep_xmls.append(os.path.splitext(basename)[0]+".pep.xml")
    with open(comet_cfg_templateFile) as fh:
        txt = fh.read()
        txt = txt.replace("DATABASE_FASTA_FILE", DDA_DB_filename)
        comet_cfg_tmp_fd = \
                           tempfile.NamedTemporaryFile(dir=worktempdir, \
                                                       mode="r+", \
                                                       delete=delete_temp_files_flag)
        comet_cfg_tmp_fd.write(txt)
        comet_cfg_tmp_fd.flush()

    pep_xmls_exists = True

    for DDA_pep_xml in DDA_pep_xmls:
        pep_xmls_exists &= os.path.exists(DDA_pep_xml)

    if pep_xmls_exists:
        print ("Comet pep xml files already exist, skipping comet.")
    else:
        cmd = [
            "/opt/comet/comet-ms",
            "-P"+comet_cfg_tmp_fd.name,
            ]
        cmd.extend(DDA_basenames)
        logline("Running pipeline command: "+" ".join(cmd))
        comet_proc = subprocess.Popen(cmd, stdout=log_fh, stderr=log_fh)
        comet_proc.wait()
        log_fh.flush()
        if comet_proc.returncode != 0:
            raise NonZeroReturnValueException(comet_proc.returncode, 'Comet')


    if os.path.exists("interact_comet_pep.xml"):
        print ("interact_comet_pep.xml file already exist, skipping merging comet files.")        
    else:
        xinteract_cmd = [
            "/opt/tpp/bin/xinteract",
            "-OARPd",
            "-dDECOY_",
            "-Ninteract_comet_pep.xml",
            ]
        xinteract_cmd.extend(DDA_pep_xmls)
        logline("Running pipeline command: "+" ".join(xinteract_cmd))
        xinteract_proc = subprocess.Popen(xinteract_cmd, stdout=log_fh, stderr=log_fh)
        xinteract_proc.wait()
        log_fh.flush()
        if xinteract_proc.returncode != 0:
            raise NonZeroReturnValueException(xinteract_proc.returncode, 'xinteract')
    return



def runXTandem(xtandem_default_input_filename, \
               DDA_DB_filename, \
               DDA_filenames):
    taxonomy_tmp_fd = \
                        tempfile.NamedTemporaryFile(dir=worktempdir, \
                                                    mode="r+", \
                                                    delete=delete_temp_files_flag)
    taxonomy_xml = '<?xml version="1.0"?>\n'
    taxonomy_xml += '<bioml label="x! taxon-to-file matching list">\n'
    taxonomy_xml += '<taxon label="DB">\n'
    taxonomy_xml += '<file format="peptide" URL="' + DDA_DB_filename + '" />\n'
    taxonomy_xml += '</taxon>\n'
    taxonomy_xml += '</bioml>\n'
    taxonomy_tmp_fd.write(taxonomy_xml)
    taxonomy_tmp_fd.flush()

    DDA_pep_xmls = {}
    for DDA_filename in DDA_filenames:
        basename = os.path.basename(DDA_filename)
        DDA_pep_xmls[DDA_filename]=os.path.splitext(basename)[0]+".tandem.pep.xml"

    tandem_outs = {}
    for DDA_filename in DDA_filenames:

        print ("Xtandem round with: " + DDA_pep_xmls[DDA_filename])
        
        if os.path.exists(DDA_pep_xmls[DDA_filename]):
            print (DDA_pep_xmls[DDA_filename] + " already exists, skipping xtandem")
            continue

        # tandem_outs[DDA_filename] = \
        #                             tempfile.NamedTemporaryFile(dir=worktempdir, \
        #                                                         mode="r+", \
        #                                                         delete=delete_temp_files_flag)

        basename = os.path.basename(DDA_filename)
        tandem_outs[DDA_filename] = os.path.splitext(basename)[0]+".TANDEM.OUTPUT.xml"
        
        input_xml = '<?xml version="1.0"?>\n'
        input_xml += '<bioml>\n'
        input_xml += '<note type="input" label="list path, default parameters">' + xtandem_default_input_filename + '</note>\n'
        input_xml += '<note type="input" label="list path, taxonomy information">'+taxonomy_tmp_fd.name+'</note>\n'
        input_xml += '<note type="input" label="protein, taxon">DB</note>\n'
        input_xml += '<note type="input" label="spectrum, path">' + DDA_filename + '</note>\n'
        input_xml += '<note type="input" label="output, path">' + tandem_outs[DDA_filename] + '</note>\n'
        input_xml += '</bioml>'
        input_tmp_fd = \
                       tempfile.NamedTemporaryFile(dir=worktempdir, \
                                                   mode="r+", \
                                                   delete=delete_temp_files_flag)
        input_tmp_fd.write(input_xml)
        input_tmp_fd.flush()
        tandem_cmd = [
            "/opt/tandem/tandem",
            input_tmp_fd.name,
            tandem_outs[DDA_filename]
            ]

        logline("Running pipeline command: "+" ".join(tandem_cmd))
        tandem_proc = subprocess.Popen(tandem_cmd, stdout=log_fh, stderr=log_fh)
        tandem_proc.wait()
        log_fh.flush()
        if tandem_proc.returncode != 0:
            raise NonZeroReturnValueException(tandem_proc.returncode, 'Tandem')

        tandemxml_cmd = [
            "/opt/tpp/bin/Tandem2XML",
            tandem_outs[DDA_filename],
            DDA_pep_xmls[DDA_filename]
            ]
        logline("Running pipeline command: "+" ".join(tandemxml_cmd))
        tandemxml_proc = subprocess.Popen(tandemxml_cmd, stdout=log_fh, stderr=log_fh)
        tandemxml_proc.wait()
        log_fh.flush()
        if tandem_proc.returncode != 0:
            raise NonZeroReturnValueException(tandemxml_proc.returncode, 'Tandem2XML')

    xinteract_cmd = [
        "/opt/tpp/bin/xinteract",
        "-OARPd",
        "-dDECOY_",
        "-Ninteract_xtandem_pep.xml",
        ]
    xinteract_cmd.extend([DDA_pep_xmls[x] for x in DDA_pep_xmls])

    logline("Running pipeline command: "+" ".join(xinteract_cmd))
    xinteract_proc = subprocess.Popen(xinteract_cmd, stdout=log_fh, stderr=log_fh)
    xinteract_proc.wait()
    log_fh.flush()
    if xinteract_proc.returncode != 0:
        raise NonZeroReturnValueException(xinteract_proc.returncode, 'xinteract')
    return



def combine_search_engine_results(decoyPrefix, \
                                  outputFilename, \
                                  DDA_DB_filename, \
                                  threads, \
                                  pepXMLs):
    
    interprophetparser_cmd = [
        "/opt/tpp/bin/InterProphetParser",
        "DECOY="+decoyPrefix,
        "THREADS="+threads,
    ]
    interprophetparser_cmd.extend(pepXMLs)
    interprophetparser_cmd.append(outputFilename)

    logline("Running pipeline command: "+" ".join(interprophetparser_cmd))
    interprophetparser_proc = subprocess.Popen(interprophetparser_cmd, stdout=log_fh, stderr=log_fh)
    interprophetparser_proc.wait()
    log_fh.flush()
    if interprophetparser_proc.returncode != 0:
        raise NonZeroReturnValueException(interprophetparser_proc.returncode, 'InterProphetParser')
    return



def buildDIALibrary(decoyPrefix, \
                    pepXML_filename, \
                    DDA_DB_filename, \
                    iRT_filename, \
                    swaths_filename, \
                    protFDR, \
                    gFDR,
                    swaths_min,
                    swaths_max):

    mayu_cmd = [
        "/opt/tpp/bin/Mayu.pl",
        "-A", pepXML_filename,
        "-C", DDA_DB_filename,
        "-E", decoyPrefix,
        "-G", gFDR,
        "-H", "51",
        "-I", "2",
        "-P", "protFDR="+str(protFDR)+":t",
    ]
    
    logline("Running pipeline command: "+" ".join(mayu_cmd))
    mayu_proc = subprocess.Popen(mayu_cmd, stdout=log_fh, stderr=log_fh)
    mayu_proc.wait()
    log_fh.flush()
    if mayu_proc.returncode != 0:
        raise NonZeroReturnValueException(mayu_proc.returncode, 'Mayu')

    shell_cmd = "cat *_psm_protFDR0*.csv |cut -f 5 -d ',' |tail -n+2 |sort -u |head -n1"

    logline("Running pipeline command: "+ shell_cmd)
    shell_proc = subprocess.Popen(shell_cmd, stdout=subprocess.PIPE, stderr=log_fh, shell=True)
    shell_proc.wait()
    log_fh.flush()
    if shell_proc.returncode != 0:
        raise NonZeroReturnValueException(shell_proc.returncode, 'shell command')

    cutoff = shell_proc.stdout.readline().decode("utf8").rstrip('\n')

    spectrast_cmd1 = [
        "/opt/tpp/bin/spectrast",
        "-cNSpecLib",
#        "-cICID-QTOF",
        "-cIHCD",
        "-cf", "\"Protein! ~ "+decoyPrefix+"\"",
        "-cP"+cutoff,
        "-c_IRT"+iRT_filename, 
        "-c_IRR", pepXML_filename 
    ]


    logline("Running pipeline command: "+" ".join(spectrast_cmd1))
    spectrast_cmd1_proc = subprocess.Popen(spectrast_cmd1, stdout=log_fh, stderr=log_fh)
    spectrast_cmd1_proc.wait()
    log_fh.flush()
    if spectrast_cmd1_proc.returncode != 0:
        raise NonZeroReturnValueException(spectrast_cmd1_proc.returncode, 'spectrast')

    spectrast_cmd2 = [
        "/opt/tpp/bin/spectrast",
        "-cNSpecLib_cons",
#        "-cICID-QTOF",
        "-cIHCD",
        "-cAC", "SpecLib.splib",
    ]

    logline("Running pipeline command: "+" ".join(spectrast_cmd2))
    spectrast_cmd2_proc = subprocess.Popen(spectrast_cmd2, stdout=log_fh, stderr=log_fh)
    spectrast_cmd2_proc.wait()
    log_fh.flush()
    if spectrast_cmd2_proc.returncode != 0:
        raise NonZeroReturnValueException(spectrast_cmd2_proc.returncode, 'spectrast')

    spectrast2tsv_cmd = [
        "spectrast2tsv.py",
        "-l", str(swaths_min)+","+str(swaths_max),
        "-s", "y,b",
        "-d",
        "-e",
        "-o", "6",
        "-n", "6", 
        "-w", swaths_filename, 
        "-k", "openswath",
        "-a", "SpecLib_cons_openswath.tsv",
        "SpecLib_cons.sptxt"
    ]    

    logline("Running pipeline command: "+" ".join(spectrast2tsv_cmd))
    spectrast2tsv_cmd_proc = subprocess.Popen(spectrast2tsv_cmd, stdout=log_fh, stderr=log_fh)
    spectrast2tsv_cmd_proc.wait()
    log_fh.flush()
    if spectrast2tsv_cmd_proc.returncode != 0:
        raise NonZeroReturnValueException(spectrast2tsv_cmd_proc.returncode, 'spectrast2tsv')


    ConvertTSVToTraML_cmd = [
        "/opt/OpenMS/bin/TargetedFileConverter",
        "-in", "SpecLib_cons_openswath.tsv",
        "-out", "SpecLib_cons.TraML"

    ]

    logline("Running pipeline command: "+" ".join(ConvertTSVToTraML_cmd))
    ConvertTSVToTraML_proc = subprocess.Popen(ConvertTSVToTraML_cmd, stdout=log_fh, stderr=log_fh)
    ConvertTSVToTraML_proc.wait()
    log_fh.flush()
    if ConvertTSVToTraML_proc.returncode != 0:
        raise NonZeroReturnValueException(ConvertTSVToTraML_proc.returncode, 'TargetedFileConverter')

    OpenSwathDecoyGenerator_cmd = [
        "/opt/OpenMS/bin/OpenSwathDecoyGenerator",
        "-in", "SpecLib_cons.TraML",
        "-out", "SpecLib_cons_decoy.TraML",
        "-method", "shuffle",
        "-append",
        "-exclude_similar",
        "-remove_unannotated"
        ]

    logline("Running pipeline command: "+" ".join(OpenSwathDecoyGenerator_cmd))
    OpenSwathDecoyGenerator_proc = subprocess.Popen(OpenSwathDecoyGenerator_cmd, stdout=log_fh, stderr=log_fh)
    OpenSwathDecoyGenerator_proc.wait()
    log_fh.flush()
    if OpenSwathDecoyGenerator_proc.returncode != 0:
        raise NonZeroReturnValueException(OpenSwathDecoyGenerator_proc.returncode, 'OpenSwathDecoyGenerator')    

    return



def buildDIAMatrix(DIA_filenames, \
                   fixed_swaths_filename, \
                   target_FDR, \
                   max_FDR, \
                   threads, \
                   irt_assay_library_traml,\
                   design_file):    


    successfull_DIA_filenames = []
    
    for DIA_filename in DIA_filenames:

        if os.path.exists(os.path.basename(DIA_filename)+"-DIA.tsv"):
            print (os.path.basename(DIA_filename)+"-DIA.tsv" + " exists, skiping openswathworkflow")
            successfull_DIA_filenames.append(DIA_filename)
            

        else:
        
            OpenSwathWorkflow_cmd = [
                "/opt/OpenMS/bin/OpenSwathWorkflow",
                "-in", DIA_filename,
                "-tr", "SpecLib_cons_decoy.TraML", 
                "-tr_irt", irt_assay_library_traml, 
                "-out_tsv", os.path.basename(DIA_filename)+"-DIA.tsv", 
                "-min_upper_edge_dist", "1",
                "-sort_swath_maps",
                "-swath_windows_file", fixed_swaths_filename,
                "-force",
                "-threads", threads

            ]

            logline("Running pipeline command: "+" ".join(OpenSwathWorkflow_cmd))
            OpenSwathWorkflow_proc = subprocess.Popen(OpenSwathWorkflow_cmd, stdout=log_fh, stderr=log_fh)
            OpenSwathWorkflow_proc.wait()
            log_fh.flush()
            if OpenSwathWorkflow_proc.returncode != 0:
                #raise NonZeroReturnValueException(OpenSwathWorkflow_proc.returncode, 'OpenSwathWorkflow')
                logline("DIA sample "+ DIA_filename +" failed. Skipping the sample.")
                
            else:
                successfull_DIA_filenames.append(DIA_filename)


    successfull_DIA_filenames_after_pyprophet = []

    for DIA_filename in successfull_DIA_filenames:

        if os.path.exists(os.path.basename(DIA_filename) + "-DIA_with_dscore.csv"):
            print (os.path.basename(DIA_filename) + "-DIA_with_dscore.csv exists, skipping pyprophet")
            successfull_DIA_filenames_after_pyprophet.append(DIA_filename)
        else:

            pyprophet_cmd = [
                "pyprophet",
                "--delim=tab",
                "--export.mayu",
                os.path.basename(DIA_filename)+"-DIA.tsv", 
                "--ignore.invalid_score_columns"
            ]

            logline("Running pipeline command: "+" ".join(pyprophet_cmd))
            pyprophet_proc = subprocess.Popen(pyprophet_cmd, stdout=log_fh, stderr=log_fh)
            pyprophet_proc.wait()
            log_fh.flush()
            if pyprophet_proc.returncode != 0:
                logline("DIA sample "+ DIA_filename +" failed. Skipping the sample.")              #raise NonZeroReturnValueException(pyprophet_proc.returncode, 'pyprophet')
            else:
                successfull_DIA_filenames_after_pyprophet.append(DIA_filename)

    feature_alignment_cmd = [
        "feature_alignment.py",
        "--method", "best_overall",
        "--realign_method", "diRT",
        "--max_rt_diff", "90",
        "--target_fdr", target_FDR,
        "--max_fdr_quality", max_FDR,
        "--out", "DIA-analysis-result.csv", 
        "--in" 
    ]
    feature_alignment_cmd.extend([ os.path.basename(x) + "-DIA_with_dscore.csv" for x in successfull_DIA_filenames_after_pyprophet])

    logline("Running pipeline command: "+" ".join(feature_alignment_cmd))
    feature_alignment_proc = subprocess.Popen(feature_alignment_cmd, stdout=log_fh, stderr=log_fh)
    feature_alignment_proc.wait()
    log_fh.flush()
    if feature_alignment_proc.returncode != 0:
        raise NonZeroReturnValueException(feature_alignment_proc.returncode, 'feature_alignment')


    swaths2stats_cmd = [
        "/opt/diatools/swaths2stats.R",
        "--input", "DIA-analysis-result.csv"
    ]

    if design_file:
        swaths2stats_cmd.extend(["--design-file", design_file])

    logline("Running pipeline command: "+" ".join(swaths2stats_cmd))
    swaths2stats_proc = subprocess.Popen(swaths2stats_cmd, stdout=log_fh, stderr=log_fh)
    swaths2stats_proc.wait()
    log_fh.flush()
    if swaths2stats_proc.returncode != 0:
        raise NonZeroReturnValueException(swaths2stats_proc.returncode, 'swaths2stats')

    return

def read_swath_windows(dia_mzML):
    
    context = ET.iterparse(dia_mzML, events=("start", "end"))

    windows = {}
    for event, elem in context:

        if event == "end" and elem.tag == '{http://psi.hupo.org/ms/mzml}isolationWindow':
            il_target = None
            il_lower = None
            il_upper = None
            for cvParam in elem.findall('{http://psi.hupo.org/ms/mzml}cvParam'):

                name = cvParam.get('name')
                value = cvParam.get('value')

                if (name == 'isolation window target m/z'):
                    il_target = value
                elif (name == 'isolation window lower offset'):
                    il_lower = value
                elif (name == 'isolation window upper offset'):
                    il_upper = value

            if not il_target in windows:
                windows[il_target] = (il_lower, il_upper)
            else:
                lower, upper = windows[il_target]
                assert (il_lower == lower)
                assert (il_upper == upper)
                return windows

    return windows


def create_swath_window_files(dia_mzML):

    windows = read_swath_windows(dia_mzML)

    swaths = []
    for x in windows:
        target_str = x
        lower_str, upper_str = windows[x]
        target = float(target_str)
        lower = float(lower_str)
        upper = float(upper_str)
        assert (lower > 0)
        assert (upper > 0)
        swaths.append((target - lower, target + upper))
        
    swaths.sort(key=lambda tup: tup[0])

    tswaths = []
    tswaths.append(swaths[0])
    for i in range(1, len(swaths)):
        if swaths[i-1][1] > swaths[i][0]:
            lower_prev, upper_prev = swaths[i-1]
            lower, upper = swaths[i]
            assert (upper_prev < upper)
            tswaths.append((upper_prev, upper))
        else:
            tswaths.append(swaths[i])

    assert (len(swaths) == len(tswaths))
            
    with open("swath-windows.txt", "w") as fh_swaths, open("truncated-swath-windows.txt", "w") as fh_tswaths:
        fh_tswaths.write("LowerOffset\tHigherOffset\n")

        for i in range(len(swaths)):
            fh_swaths.write(str(swaths[i][0]) + "\t" + str(swaths[i][1])  + "\n")
            fh_tswaths.write(str(tswaths[i][0]) + "\t" + str(tswaths[i][1])  + "\n")

    return swaths, tswaths
            
    
if __name__=="__main__":

    parser = argparse.ArgumentParser(description='DIA Pipeline')

    parser.add_argument('--in-DDA-mzXML',
                        nargs='+',
                        action='store',
                        dest='in_dda_mzXML',
                        required=True,
                        default=None,
                        help='Raw MSMS files for DDA library')

    parser.add_argument('--in-DIA-mzML',
                        nargs='+',
                        action='store',
                        dest='in_dia_mzML',
                        required=False,
                        default=None,
                        help='Raw MSMS DIA files')

    parser.add_argument('--worktempdir', 
                        action='store',
                        dest='worktempdir',
                        required=False,
                        default="./",
                        help='directory for tmp')

    parser.add_argument('--db', 
                        action='store',
                        dest='db',
                        required=False,
                        default=None,
                        help='Fasta file of the database of peptide search space')

    parser.add_argument('--db-with-decoys', 
                        action='store',
                        dest='db_with_decoys',
                        required=False,
                        default=None,
                        help='Fasta file of the database of peptide search space has already decoys')

    parser.add_argument('--comet-cfg-template', 
                        action='store',
                        dest='comet_cfg_template',
                        default="/opt/diatools/comet.params.template",
                        required=False,
                        help='Comet config template file.')

    parser.add_argument('--xtandem-cfg-template', 
                        action='store',
                        dest='xtandem_cfg_template',
                        default="/opt/diatools/xtandem_settings.xml",
                        required=False,
                        help='XTandem config template file.')

    # parser.add_argument('--out', 
    #                     action='store',
    #                     dest='out',
    #                     required=True,
    #                     default=None,
    #                     help='Output file to be written')

    parser.add_argument('--library-FDR', 
                        action='store',
                        dest='library_FDR',
                        required=False,
                        default="0.01",
                        help='Set FDR used in spectral library build. [default: 0.01]')

    parser.add_argument('--feature-alignment-FDR', 
                        nargs='+',
                        action='store',
                        dest='feature_alignment_FDR',
                        required=False,
                        default=["0.01", "0.05"],
                        help='Set target and max FDR used in TRIC alignment in diRT mode. [default: [0.01, 0.05]]')

    parser.add_argument('--threads', 
                        action='store',
                        dest='threads',
                        required=False,
                        default="4",
                        help='Set amount of threads. [default: 4]')

    # parser.add_argument('--iRT-file', 
    #                     action='store',
    #                     dest='iRT_file',
    #                     required=True,
    #                     help='iRT file.')

    # parser.add_argument('--iRT-assay-library', 
    #                     action='store',
    #                     dest='iRT_assay_library',
    #                     required=True,
    #                     help='iRT assay library [TraML].')

    # parser.add_argument('--swaths-file', 
    #                     action='store',
    #                     dest='swaths_file',
    #                     default=None,
    #                     required=False,
    #                     help='SWATH windows in RAW data.')

    # parser.add_argument('--fixed-swaths-file', 
    #                     action='store',
    #                     dest='fixed_swaths_file',
    #                     default=None,
    #                     required=False,
    #                     help='SWATH windows with fixed offsets..')

    parser.add_argument('--logfile', 
                        action='store',
                        dest='logfile',
                        required=False,
                        default="log.txt",
                        help='Log filename. [default: log.txt]')

    parser.add_argument('--design-file', 
                        action='store',
                        dest='design_file',
                        required=False,
                        default=None,
                        help='Log filename. [default: log.txt]')

    parser.add_argument('--retain-tmp-files', 
                        action='store_true',
                        dest='retain_tmp_files',
                        required=False,
                        default=False,
                        help='Dont delete temp files.')

    parser.add_argument('--use-msgf', 
                        action='store_true',
                        dest='use_msgf',
                        required=False,
                        default=False,
                        help='Use MS-GF+ search engine. [Experimental feature.]')

    parser.add_argument('--use-comet', 
                        action='store_true',
                        dest='use_comet',
                        required=False,
                        default=False,
                        help='Use Comet search engine.')

    parser.add_argument('--use-xtandem', 
                        action='store_true',
                        dest='use_xtandem',
                        required=False,
                        default=False,
                        help='Use X!Tandem search engine.')

    args = parser.parse_args()

    worktempdir = args.worktempdir

    delete_temp_files_flag = not args.retain_tmp_files
    
    log_fh = open(args.logfile, "w")
    logline("Pipeline command line: " + " ".join(sys.argv))

    if args.db:
        with open(args.db, "r") as fh:
            decoy_db_file = decoyDB(fh)
    elif args.db_with_decoys:
        decoy_db_file = args.db_with_decoys
    else:
        print("Need to provide sequence database.")
        exit(1)

    swaths_min = 0
    swaths_max = 0
       
    if args.in_dia_mzML:
       swaths, tswaths = create_swath_window_files(args.in_dia_mzML[0])
       swaths_min = swaths[0][0]
       swaths_max = swaths[-1][1]

    assert (swaths_min < swaths_max)
       
    pepXMLs = []


    if args.use_msgf:
        runMSGFPlus(decoy_db_file, args.in_dda_mzXML, args.threads)
        pepXMLs.append("interact_msgf_pep.xml")
        
    if args.use_comet:
        runComet(args.comet_cfg_template, decoy_db_file, args.in_dda_mzXML)
        pepXMLs.append("interact_comet_pep.xml")

    if args.use_xtandem:
        runXTandem(args.xtandem_cfg_template, decoy_db_file, args.in_dda_mzXML)
        pepXMLs.append("interact_xtandem_pep.xml")


    if len(pepXMLs) > 1:
        pepXMLFile = "iprofet.peps.xml"
        combine_search_engine_results("DECOY_", \
                                      pepXMLFile, \
                                      decoy_db_file, \
                                      args.threads, \
                                      pepXMLs)
    elif len(pepXMLs) == 1:
        pepXMLFile = pepXMLs[0]
    else:
        print("No search engine results. ")
        sys.exit(1)
        
    buildDIALibrary("DECOY_", \
                    pepXMLFile, \
                    decoy_db_file, \
                    "/opt/diatools/iRT.txt", \
                    "swath-windows.txt", \
                    args.library_FDR, \
                    args.library_FDR, \
                    swaths_min,
                    swaths_max)


    if args.in_dia_mzML:

        assert len(args.feature_alignment_FDR) == 2
        
        buildDIAMatrix(args.in_dia_mzML, \
                       "truncated-swath-windows.txt", \
                       args.feature_alignment_FDR[0], \
                       args.feature_alignment_FDR[1], \
                       args.threads, \
                       "/opt/diatools/iRTAssayLibrary.TraML",\
                       args.design_file)


    sys.exit(0)



