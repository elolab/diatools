#! /usr/bin/env python3

import annotation
import json
import os
import shutil
import pandas as pd
import time
import argparse
import sys

result_root = "/run-files/"

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='DIA Matrix Annotation Utility')
    parser.add_argument('--project-name',
                        action='store',
                        dest='project_name',
                        required=True,
                        help='Project to be annotated.')

    parser.add_argument('--annotation-files',
                        nargs='+',
                        action='store',
                        dest='annotation_files',
                        required=True,
                        help='TSV file containing annotation for database fasta identifier.')

    parser.add_argument('--id-column',
                        action='store',
                        dest='id_key',
                        required=True,
                        help='Annotation column name for protein ID. Should match sequence database fasta identifier.')

    parser.add_argument('--threshold',
                        action='store',
                        dest='ambiguous_threshold',
                        default="2",
                        required=False,
                        help='Threshold of different annotations until labeled as ambiguous [Default 2].')

    parser.add_argument('--merge-unimods',
                        action='store_true',
                        dest='merge_unimods',
                        default=False,
                        required=False,
                        help='Merge unimods, so that peptides will become unique by their sequences. [Default: No Merge].')

    
    args = parser.parse_args()
    cwd = os.path.join(result_root, args.project_name)
    log_name = "log.txt"

    with open(os.path.join(cwd, log_name), "w") as log_fh:
    
        dicts = None
        for filename in args.annotation_files:
            id_key = args.id_key  
            dicts = annotation.load_annotations(\
                None,\
                log_fh,\
                None,\
                id_key,\
                os.path.join(result_root, filename),\
                dicts)

        df = None
        df = annotation.read_openswathfile(\
            None,\
            log_fh,\
            None,\
            os.path.join(result_root, args.project_name, "DIA-analysis-result.csv"))

        annotation.annotate_df(\
                None,\
                log_fh,\
                None,\
                df,\
                dicts,\
                os.path.join(result_root, args.project_name, "matrix.tsv"),\
                os.path.join(result_root, args.project_name, "annotations.tsv"),\
                args.ambiguous_threshold,\
                args.merge_unimods)

