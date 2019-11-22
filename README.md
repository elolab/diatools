### About

Diatools is a software package for analyzing mass-spectrometer data acquired using data independent acquisition (DIA) mode. Currently, diatools consists of a single workflow for building a spectral library from data dependent aquisition mode (DDA) data and for analyzing DIA samples with the spectral library. The spectral library is built according to the protocol described in Schubert et al. 2015. The DIA data analysis is done with OpenSWATH software and the end result is a peptide intensity matrix. Optionally, a differential expression analysis of sample groups is performed.

Diatools runs on GNU/Linux, Windows and macOS platforms. However, the conversion of the mass-spectrometer proprietary raw files to open formats has to be done on Windows operating system.

Having at least 128GB of RAM is recommended. However, the required amount of memory depends greatly on the size of protein sequence database.

### Download the diatools workflow.

Diatools is designed to run under a Docker container. After installing Docker software, download the diatools docker image from Docker Hub. 

```
$ docker pull compbiomed/diatools
```

### Create a folder `dataset` on the machine where the data-analysis is done and create the following subfolders under it:

* config
* DDA
* DIA
* ref
* out 

### Convert the raw mass-spectrometer files to open format

This step needs to be done on a Windows platform using ProteoWizard software.

Note. Make sure filenames do not contain spaces. Convert all spaces into underscore character.

Convert the DDA raw files to mzXML format and do peak picking:

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

Convert the DIA raw files to mzML format by using the MSConvert program from the ProteoWizard software. Use the following options:

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

### Construct a database FASTA file

Create a sequence database FASTA file that contains following protein sequences:

* Proteins of interest (for example Swiss-Prot Human)
* IRT peptides (Biognosys|iRT-Kit_WR_fusion)
* Peptides related to lysis (Uniprot ID: Q7M135)
* Digestion enzyme (typically Trypsin (Uniprot ID: P00761))
* Possible contaminants 

Copy the FASTA file to the `dataset/ref` folder with the name "sequences.fasta".

### Customize peptide search parameters of the spectral library (OPTIONAL)

The default parameters are for a nanoflow HPLC system (Easy-nLC1200, Thermo Fisher Scientific) coupled to a Q Exactive HF mass spectrometer (Thermo Fisher Scientific) equipped with a nano-electrospray ionization source.

Below is the summary of the settings:

* Precursor mass tolerance: 10 ppm
* Fragment ion tolerance: 0.02 Da
* Cleavage site: Trypsin_P
* Fixed modification: Carbamidomethyl (C)
* Variable modification: Oxidation (M)

The search parameters can be customized by modifying `comet.params.template` and `xtandem_settings.xml` and copying the files to `dataset/config`. The modified files are given to the pipeline with the following extra parameters:

```
--comet-cfg-template config/comet.params.template
--xtandem-cfg-template config/xtandem_settings.xml
```


### Run the analysis 

Create a spectral library from the DDA files and analyze the DIA files against the library:

```
$ docker run --rm \
-v /LOCALPATH/dataset/:/dataset \
--workdir /dataset/out \
-u $(id -u):$(id -g) \
compbiomed/diatools \
/opt/diatools/dia-pipeline.py \
--in-DDA-mzXML ../DDA/*.mzXML \
--in-DIA-mzML ../DIA/*.mzML \
--db ../ref/sequences.fasta \
--use-comet \
--use-xtandem 
```

Note, there might be need to modify the command above slightly if operating system is not Linux. For example, dataset path in windows command prompt should be: `-v //c/LOCALPATH/dataset:/dataset`, where c is the drive letter. Furthermore on windows command prompt `-u $(id -u):$(id -g)` parameter must be omitted.

After the pipeline has completed, the "out" folder contains `dia-peptide-matrix.tsv` and `dia-protein-matrix.tsv` files. The files are TSV formatted and can be loaded to spreadsheet programs like MS Excel or to a statistical analysis programs like R. The `dia-peptide-matrix.tsv` contains detected peptides and their intensity for each of the samples. The first column contains peptide sequence and a list of possible source proteins. Rest of the columns indicate samples and contain peptide intensity value in each of the samples. Respectively `dia-protein-matrix.tsv` contains intensity values, but at protein level.

To perform the optional differential expression analysis between sample groups, the groups must be provided using an additional parameter in the command:

```
--design-file <designFilename>
```

The design file must be defined as a tab-separated file (see `example-design-file.tsv`), where the column Filename refers to the SWATH-MS filename of a sample, the column Condition is the group to which the sample belongs, the column BioReplicate refers to the biological replicate, and the column Run to the MS run.

### Appendix - Get comprehensive list of pipeline parameters and descriptions

```
docker run --rm compbiomed/diatools /opt/diatools/dia-pipeline.py --help

```
### Appendix - Modify false discovery rate

False discovery rate (FDR) of the library building can be adjusted with `--library-FDR` parameter. TRIC feature alignment FDR can be adjusted with `--feature-alignment-FDR` parameter. A comprehensive list of pipeline parameters can be obtained with following command:

### Appendix - Deploy the Docker image as a container with SSH-access.

The build process might take a while. Once the image build is completed create a container using the image by running the command below:

```
$ docker run \
-d \
-p 2222:22 \
--cap-add SYS_ADMIN \
--device /dev/fuse \
--security-opt apparmor:unconfined \
openms \
/usr/sbin/sshd -D
```

(Optional) Copy ssh-key to the running container. If this step is done, password is not asked at login. The password being asked is: "Ymko7WFcLfe4U".

```
ssh-copy-id "-p 222 root@localhost"
```

The environment is now up and running. There is an SSH-server listening at port 2222. Log into the environment by using a persistent screen session:

```
ssh -t -p 2222 root@localhost screen -R -d
```

Login. If the ssh-key is not copied you need to give the root password: "Ymko7WFcLfe4U". Now you should be in the environment. Mount the path with your data from some machine over ssh. You can replace the ip address `172.17.0.1` with your machine address that contains the data.

```
# sshfs -o allow_other my_user_name@172.17.0.1:/my/path/to/datafiles /mnt
```

Now the environment should be ready and your data can be found from `/mnt`. 

### Appendix - Build the diatools Docker image by using Dockerfile in this repository.

```
$ docker build -t diatools . -f Dockerfile
```

### Appendix - Run analysis with Singularity instead of Docker


Convert Docker image to Singularity image: 

```
$ singularity build diatools-1.0.sif docker-archive://diatools-docker.img
```

Run diatools:

```
$ singularity exec \
--bind /LOCALPATH/data/:/metaproteomics diatools-1.0.sif \
/opt/diatools/dia-pipeline.py \
--in-DDA-mzXML /metaproteomics/lib1.mzXML /metaproteomics/lib2.mzXML \
--in-DIA-mzML /metaproteomics/sample1.mzML /metaproteomics/sample2.mzML \
--use-comet \
--use-xtandem \
--db sequences.fasta
```


