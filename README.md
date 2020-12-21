# DIAtools 2.0

### About

DIAtools 2.0 is a software package for analyzing mass spectrometry data acquired using *data independent acquisition* (DIA) mode. It runs on x86/64 platforms supported by Docker. Having at least 128 GB RAM is recommended running the example dataset presented in this Documentation.

### Download the DIAtools 2.0

DIAtools 2.0 is designed to run under a Docker container. After installing Docker software, download the DIAtools 2.0 image from Docker Hub. 

```
$ docker pull elolab/diatools:2.0
```

### Download example data (12mix)

Download the following 12mix DIA sample files from ProteomeXchange Consortium, PRIDE repository (https://www.ebi.ac.uk/pride/) identifier PXD008738.

* 170413_12mix_DIA_14.raw
* 170413_12mix_DIA_15.raw
* 170413_12mix_DIA_16.raw

### Convert the raw mass spectrometry files to open format

This step needs to be done on a Windows platform using the ProteoWizard software.

Convert the DIA raw files to mzML format using the MSConvert program from the ProteoWizard software with the following options:

* Output format: mzML
* Extension: empty
* Binary encoding precision: 64bit
* Write index: checked
* TPP compatibility: checked
* Use zlib compression: unchecked
* Package in gzip: unchecked
* Use numpress linear compression: unchecked
* Use numpress short logged float compression: unchecked
* Use numpress short positive integer compression: unchecked
* Only titleMaker filter


### Create and populate the following folder structure

Create the following folder structure under a selected local path, referred to as LOCALPATH here.

* Create folder `out` for the results.
* Create folders `data/12mix/DDA`, `data/12mix/DIA` and `data/ref`.
* Copy converted mzML files to `data/12mix/DIA`.
* Copy and unpack the integrated non-redundant gene catalog (IGC, amino acid sequences, fasta) from ftp://ftp.cngb.org/pub/SciRAID/Microbiome/humanGut_9.9M/GeneCatalog/IGC.pep.gz to `data/ref`.
* Download human proteins as fasta from https://www.uniprot.org/ to `data/ref`. 
* Download trypsin ("sp|P00761|TRYP_PIG Trypsin") amino acid sequence as fasta to `data/ref`.
* Download lysis related enzyme ("sp|Q7M135|LYSC_LYSEN Lysyl endopeptidase OS=Lysobacter enzymogenes PE=1 SV=1") amino acid sequence as fasta to `data/ref`.
* Download iRT peptides (Biognosys|iRT-Kit_WR_fusion) as fasta to `data/ref`.


### Customize peptide search parameters of the spectral library (OPTIONAL)

The default parameters are for a nanoflow HPLC system (Easy-nLC1200, Thermo Fisher Scientific) coupled to a Q Exactive HF mass spectrometer (Thermo Fisher Scientific) equipped with a nano-electrospray ionization source.

Below is the summary of the settings:

* Precursor mass tolerance: 10 ppm
* Fragment ion tolerance: 0.02 Da
* Cleavage site: Trypsin_P
* Fixed modification: Carbamidomethyl (C)
* Variable modification: Oxidation (M)

The search parameters can be customized by modifying `comet.params.template` and `xtandem_settings.xml` and copying the files to `data/config`. The modified files are provided with the following extra parameters:

```
--comet-cfg-template config/comet.params.template
--xtandem-cfg-template config/xtandem_settings.xml
```


### Run the analysis 

Analyze the DIA files:

```
$ docker run -it --rm \
-u $(id -u):$(id -g) \
-v /LOCALPATH/data/:/data \
-v /LOCALPATH/out:/run-files \
diatools:2.0 /opt/diatools/dia-pipeline.py \
--project-name my-first-analysis \
--sample-data /data/12mix/DIA/mzML/170413_12mix_DIA_14.mzML /data/12mix/DIA/mzML/170413_12mix_DIA_15.mzML /data/12mix/DIA/mzML/170413_12mix_DIA_16.mzML
--databases /data/ref/IGC.pep.fasta /data/ref/irtfusion.fasta /data/ref/uniprot_human.fasta /data/ref/trypsin.fasta /data/ref/Q7M135.fasta
```

Note, there might be need to modify the command above slightly if the operating system is not Linux. For example, dataset path in Windows command prompt should be: `-v //c/LOCALPATH/data:/data`, where c is the drive letter. Furthermore on Windows command prompt `-u $(id -u):$(id -g)` parameter must be omitted. \
\
After the processing has completed, the "out" folder contains `dia-peptide-matrix.tsv` and `dia-protein-matrix.tsv` files. The files are TSV formatted and can be loaded to spreadsheet programs like MS Excel or to a statistical analysis program like R. The `dia-peptide-matrix.tsv` contains the detected peptides and their intensity for each of the samples. The first column contains the peptide sequence and a list of possible source proteins. The rest of the columns indicate the samples and contain the peptide intensity values in each sample. Similarly, `dia-protein-matrix.tsv` contains the intensity values at the protein level. \
\
To perform an optional differential expression analysis between the sample groups, the groups must be provided using an additional parameter in the command: --design-file <designFilename>. The design file must be defined as a tab-separated file (see `example-design-file.tsv`), where the column Filename refers to the filename of a sample, the column Condition is the group to which the sample belongs, the column BioReplicate refers to the biological replicate, and the column Run to the MS run.

### Annotate the peptide intensity matrix

```
$ docker run -it --rm \
-u $(id -u):$(id -g) \
-v /LOCALPATH/data/:/data \
-v /results:/run-files \
diatools:2.0 /opt/diatools/annotate-matrix.py \
--project-name my-first-analysis \
--annotation-files /data/ref/IGC.annotation.summary.v2-with-header.tsv \
--id-column 'Gene Name'
```
There are two optional parameters
* --threshold (The number of different annotations after which a peptide is labeled ambiguous. Default is 2.)
* --merge-unimods (Merge modifications by summing the intensities of peptides with the same amino acid sequence. Peptide sequences become unique.)

Note, IGC.annotation.summary.v2-with-header.tsv is IGC.annotation.summary.v2.tsv file, available at IGC homepage, with the following column names as the first row:

* Gene ID
* Gene Name
* Gene Length
* Gene Completeness Status
* Cohort Origin
* Taxonomic Annotation(Phylum Level)
* Taxonomic Annotation(Genus Level)
* KEGG Annotation
* eggNOG Annotation
* Sample Occurence Frequency
* Individual Occurence Frequency
* KEGG Functional Categories
* eggNOG Functional Categories
* Cohort Assembled


## Appendix - Use DDA data for the library (OPTIONAL)

Download the following 12mix DDA sample files for library construction from ProteomeXchange Consortium, PRIDE repository (https://www.ebi.ac.uk/pride/) identifier PXD008738:

* 170412_12mix_DDA_library_stock_2_2.raw
* 170412_12mix_DDA_library_stock_2_3.raw
* 170412_12mix_DDA_library_stock_2_4.raw  

Convert the DDA raw files to mzXML format on a Windows platform using the ProteoWizard software.

```
FOR %i IN (*.raw) DO \
"\Program Files\ProteoWizard\ProteoWizard 3.0.11252\qtofpeakpicker.exe" \
--resolution=2000 \
--area=1 \
--threshold=1 \
--smoothwidth=1.1 \
--in %i \
--out %~ni.mzXML
```

Run the previously described DIA analysis steps with the following modifications:

Copy converted mzXML files to `/LOCALPATH/data/12mix/DDA`

Add the following additional parameter to dia-pipeline.py indicating that the library data comes from DDA samples and run the analysis.

```
--library-data /data/12mix/DDA/mzXML-peak-picked/170412_12mix_DDA_library_stock_2_2.mzXML /data/12mix/DDA/mzXML-peak-picked/170412_12mix_DDA_library_stock_2_3.mzXML /data/12mix/DDA/mzXML-peak-picked/170412_12mix_DDA_library_stock_2_4.mzXML  
```

### Appendix - Modify false discovery rate (OPTIONAL)

False discovery rate (FDR) of the library building can be adjusted with `--library-FDR` parameter. TRIC feature alignment FDR can be adjusted with `--feature-alignment-FDR` parameter.


### Appendix - Build the DIAtools 2.0 Docker image using the Dockerfile in this repository.

```
$ docker build -t diatools . -f Dockerfile
```

