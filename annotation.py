#! /usr/bin/env python3

import sys
import os
import numpy as np
import pandas as pd
import re

from progress import Progress

from Bio import SeqIO


def load_genbank_annotations(gb_file, descriptions, dicts):

    # descriptions = [
    #     {
    #         "type": "Protein",
    #         "qualifiers": ["EC_number", "Product"]
    #     },
    #     {
    #         "type": "source",
    #         "qualifiers": ["organism"]
    #     },
    # ]

    
    annotations = {}
    records = SeqIO.parse(gb_file, "genbank")
    for record in records:
        ID = record.id
        entries = {}

        for feature in record.features:
            for desc in descriptions:
                if feature.type == desc["type"]:
                    for qualifier in desc["qualifiers"]:
                        if qualifier in feature.qualifiers:
                            entries[feature.type] = feature.qualifiers[qualifier]

        annotations[ID]=entries


    for ID in annotations:
        features = entries[ID]

        for key in features:
            value = features[key]
            if value:
                if key not in dicts:
                    dicts[key] = {}
                if isinstance(value, list):
                    dicts[key][ID] = ";".join(value)
                else:
                    dicts[key][ID] = value
        
    return dicts


def load_annotations(event, log_fh, progressData, ID_key, anno_file, dicts):
    
    progress = Progress(progressData, "percentage-indicator")

    df = pd.read_csv(anno_file, sep='\t')

    if dicts is None:
        dicts = {}

    fields = df.columns.tolist()

    fields.remove(ID_key)

    rows, columns = df.shape

    step = 0
    n_steps = rows

    for index in df.index.values:
        row = df.loc[index, :]
        ID = row[ID_key]
        for field in fields:
            if field not in dicts:
                dicts[field] = {}
            dicts[field][ID] = str(row[field]).strip()
        step += 1
        progress.update_n_of_m(step, n_steps)
        if event and event.kill_flag:
            return


    # for row in range(0, rows):

    #     ID = str(df[ID_key][row]).strip()

    #     for field in fields:
    #         if field not in dicts:
    #             dicts[field] = {}
    #         dicts[field][ID] = str(df[field][row]).strip()


    progress.update_n_of_m(n_steps, n_steps)
    progress.ready()

    return dicts


def annotate_df(
        event, 
        log_fh, 
        progressData,
        df,
        dicts,
        out_matrix_filename,
        out_annot_filename,
        ambiguous_threshold,
        merge_unimods):

    progress = Progress(progressData, "percentage-indicator")

    nrows, ncols = df.shape

    sorted_samplenames = df.columns.tolist()
    sorted_samplenames.remove('FullPeptideName')
    sorted_samplenames.remove('Proteins')

    annot_colnames = list(dicts)

    for annot_colname in annot_colnames:
        df[annot_colname]=["" for x in range(nrows)]


    step = 0
    n_steps = nrows

    for row in range(0, nrows):

        sets = {}
        
        for colname in annot_colnames:
            if colname not in sets:
                sets[colname] = set()

        fullPeptideName = df.loc[df.index[row], 'FullPeptideName']

        if merge_unimods:
            df.at[df.index[row], "Peptide"] = re.sub(r" ?\([^)]+\)", "", fullPeptideName)
        else:
            df.at[df.index[row], "Peptide"] = fullPeptideName

        l = df.loc[df.index[row], 'Proteins'].split(";")

        l = [x.split("|")[0] for x in l] # UGLY filtering

        for ID in l:
            for k in dicts:
                if ID in dicts[k]:
                    sets[k].add(dicts[k][ID])

        L = {}
        for k in annot_colnames:
            L[k] = list(sets[k])

            if len(L[k]) > 1 and "unknown" in L[k]:
                L[k].remove('unknown')

            if len(L[k]) == 1:
                df.at[df.index[row], k] = L[k][0]
            elif len(L[k]) > 1:
                if not ambiguous_threshold or (ambiguous_threshold and len(L[k]) < int(ambiguous_threshold)):
                    df.at[df.index[row], k] = ";".join(L[k])
                else:
                    df.at[df.index[row], k] = "ambiguous"
            else:
                df.at[df.index[row], k] = "unknown"

        step += 1
        progress.update_n_of_m(step, n_steps)
        if event and event.kill_flag:
            return

    # df.to_csv(out_mixedmatrix_filename, sep="\t", index=False)

    if out_annot_filename:
        annot_df_cols = ['FullPeptideName','Proteins']
        annot_df_cols.extend(annot_colnames)
        annot_df = df.filter(items=annot_df_cols)
        annot_df.to_csv(out_annot_filename, sep="\t", index=False)

    if out_matrix_filename:
        df_cols = ['FullPeptideName'] 
        df_cols.extend(sorted_samplenames)
        df = df.filter(df_cols)
        df.to_csv(out_matrix_filename, sep="\t", index=False)

    progress.update_n_of_m(n_steps, n_steps)
    progress.ready()

    return 

def read_openswathfile(
    event, 
    log_fh, 
    progressData,
    in_filename):

    progress = Progress(progressData, "percentage-indicator")

    entries = {}
    filenames = []

    df = pd.read_csv(in_filename, sep="\t")
    df = df[df['decoy'] == 0]

    df['ProteinName'] = df['ProteinName'].apply(lambda x: ";".join(x.split('/')[1:]))
    
    nrows, ncols = df.shape

    step = 0
    n_steps = nrows * 2

    for i in range(1, nrows):
        row_df = df.iloc[[i],:]

        fields = {
                    "Sequence":None,
                    "FullPeptideName":None,
                    "Charge":None,
                    "m/z":None,
                    "Intensity":None,
                    "ProteinName":None,
                    "filename": None,
        }

        for field in fields:
            fields[field] = row_df[field].iloc[0]

        fields['filename'] = os.path.basename(fields['filename']) 
        if not fields['filename'] in filenames:
            filenames.append(fields['filename'])

        indexTuple = (fields['FullPeptideName'], fields['Charge'])

        if not indexTuple in entries:
            entries[indexTuple] = {}

        if not fields['filename'] in entries[indexTuple]:
            entries[indexTuple][fields['filename']] = fields
        else:
            print ("Error: already contains following an entry ")

        step += 1
        progress.update_n_of_m(step, n_steps)

        if event and event.kill_flag:
            return None


    #colnames = ["FullPeptideName", "Sequence", "Charge", "m/z" ,"ProteinName"]

    colnames = ["Sequence", "ProteinName"]
    intensity_df = pd.DataFrame(columns = colnames + filenames)

    n_steps = nrows + len(entries)

    for key_tuple in entries:

        entry = entries[key_tuple]
        content = {}
        for filename in filenames:

            if filename in entry:

                for colname in colnames:

                        if not colname in content:
                            content[colname] = entry[filename][colname]
                        else:
                            assert entry[filename][colname] == entry[filename][colname]

                content[filename] = entry[filename]["Intensity"]
            else:
                content[filename] = 0

        #content["FullPeptideName"] = content["FullPeptideName"] + "_" + str(content["Charge"])

        intensity_df = intensity_df.append(
            content, 
            ignore_index=True
        )

        step += 1
        progress.update_n_of_m(step, n_steps)

        if event and event.kill_flag:
            return None

    rules_dict = {"ProteinName" : lambda x: ";".join(x)}
    for filename in filenames:
                     rules_dict[filename] = "sum"

    intensity_df = intensity_df.groupby("Sequence", as_index=False).agg(rules_dict)
    intensity_df.rename(columns={"Sequence":"FullPeptideName", "ProteinName":"Proteins"}, inplace=True)
    intensity_df['Proteins'] = intensity_df['Proteins'].apply(lambda x: ";".join(set(x.split(';'))))

    progress.update_n_of_m(n_steps, n_steps)
    progress.ready()

    return intensity_df
