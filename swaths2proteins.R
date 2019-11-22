#!/usr/bin/env Rscript

# Example of Design Matrix of aLFQ
#Filename        Condition       BioReplicate    Run
#170413_12mix_DIA_3.mzML-DIA_with_dscore.csv     regular 1       1
#170413_12mix_DIA_10.mzML-DIA_with_dscore.csv    regular 1       2
#170413_12mix_DIA_13.mzML-DIA_with_dscore.csv    shredder        2       3
#170413_12mix_DIA_14.mzML-DIA_with_dscore.csv    shredder        2       4
#170413_12mix_DIA_15.mzML-DIA_with_dscore.csv    shredder        2       5
#170413_12mix_DIA_16.mzML-DIA_with_dscore.csv    shredder        2       6
#170413_12mix_DIA_17.mzML-DIA_with_dscore.csv    shredder        2       7
#170413_12mix_DIA_18.mzML-DIA_with_dscore.csv    regular 2       8
#170412_12mix_DIA_19.mzML-DIA_with_dscore.csv    regular 2       9
#170413_12mix_DIA_19.mzML-DIA_with_dscore.csv    regular 2       10
#170413_12mix_DIA_20.mzML-DIA_with_dscore.csv    regular 2       11


suppressPackageStartupMessages(library(SWATH2stats))
suppressPackageStartupMessages(library(data.table))
suppressPackageStartupMessages(library("argparse"))
suppressPackageStartupMessages(library("aLFQ"))
suppressPackageStartupMessages(library("tidyr"))


parser = ArgumentParser()

parser$add_argument("--input", 
                    help = "Result file from OpenSWATH")

parser$add_argument("--design", 
                    help = "Design Matrix for aLFQ")

parser$add_argument("--output",
                    help = "Output file for DIA-matrix with inferred proteins")

args = parser$parse_args()

# Main Entry

if (is.null(args$input)) {
  print("--input is missing")
  stop()
}

if (is.null(args$design)) {
  print("--design is missing")
  stop()
}

if (is.null(args$output)) {
  print("--output is missing")
  stop()
}


#data = data.frame(fread(args$input, sep='\t', header=TRUE))
#data = reduce_OpenSWATH_output(data)
#data = data[grep('iRT', data$ProteinName, invert=TRUE),]
#data = data[grep('DECOY_', data$ProteinName, invert=TRUE),]
#protein_matrix = write_matrix_proteins(data,filename = args$output, rm.decoy = TRUE)
#write.table(protein_matrix, sep="\t", file = args$output, row.names=FALSE)

mydata = data.frame(fread(args$input, sep='\t', header=TRUE))
mydata = reduce_OpenSWATH_output(mydata)
mydata = mydata[grep('iRT', mydata$ProteinName, invert=TRUE),]
mydata = mydata[grep('DECOY_', mydata$ProteinName, invert=TRUE),]
studydesign = read.table(args$design, header=T, sep="\t")
mydata.annotated = sample_annotation(mydata, studydesign)

mscore = mscore4protfdr(mydata, FFT = 0.25, fdr_target = 0.05)
mydata.filtered = filter_mscore(mydata.annotated, mscore)
#mydata.filteredx = filter_on_max_peptides(mydata.filtered, n_peptides = 10)
mydata.filtered2 = filter_on_min_peptides(mydata.filtered, n_peptides = 2)
mydata.filtered3 = filter_proteotypic_peptides(mydata.filtered2)


mydata.transition = disaggregate(mydata.filtered3)
myaLFQ.input = convert4aLFQ(mydata.transition)

prots = ProteinInference(myaLFQ.input,
                          peptide_method = 'top',
                          peptide_topx = 3,
                          peptide_strictness = 'loose',
                          peptide_summary = 'mean',
                          transition_topx = 3,
                          transition_strictness = 'loose',
                          transition_summary = 'sum',
                          fasta = NA,
                          model = NA,
                          combine_precursors = FALSE)
                          
tmp_matrix = spread(prots, run_id, response)
protein_matrix = tmp_matrix[,names(tmp_matrix) != "concentration"]
write.table(protein_matrix, sep="\t", file = args$output, row.names=FALSE)


