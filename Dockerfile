FROM ubuntu:18.04

MAINTAINER Sami

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y apt-utils

RUN apt-get update \
    && apt-get -y install wget\
    && apt-get -y install git\
    && apt-get -y install emacs-nox\
    && apt-get -y install build-essential\
    && apt-get -y install openssh-server\
    && apt-get -y install sshfs\
    && apt-get -y install tandem-mass\
    && apt-get -y install openjdk-8-jdk\
    && apt-get -y install screen\
    && apt-get -y install xpra\
    && apt-get -y install g++\
    && apt-get -y install zlib1g-dev\
    && apt-get -y install libghc-bzlib-dev\
    && apt-get -y install gnuplot\
    && apt-get -y install unzip\
    && apt-get -y install locales\
    && apt-get -y install expat\
    && apt-get -y install libexpat1-dev\
    && apt-get -y install subversion\
    && apt-get -y install comet-ms\
    && apt-get -y install libfindbin-libs-perl\
    && apt-get -y install libxml-parser-perl\
    && apt-get -y install libtool-bin\
    && apt-get -y install curl\
    && apt-get -y install sudo \
    && apt-get -y install cmake\
    && apt-get -y install gfortran-multilib\
    && apt-get -y install libqt4-dev
    
RUN apt-get -y install r-base\
    && apt-get -y install r-base-dev\
    && apt-get -y install r-cran-data.table\
    && apt-get -y install r-bioc-biobase\
    && apt-get -y install r-bioc-biocgenerics\
    && apt-get -y install r-bioc-deseq2\
    && apt-get -y install r-cran-randomforest\
    && apt-get -y install r-cran-mvtnorm\
    && apt-get -y install r-bioc-biocinstaller\
    && apt-get -y install r-cran-ade4\
    && apt-get -y install r-cran-minqa

RUN apt-get -y install python3-pandas \
    && apt-get -y install python3-pandas-lib \
    && apt-get -y install python-pip\
    && apt-get -y install python3-pip\
    && apt-get -y install python-pymzml\
    && apt-get -y install python3-pymzml\
    && apt-get -y install python3-psutil\
    && apt-get -y install python3-virtualenv\
    && apt-get -y install python3-pyramid\
    && apt-get -y install python3-cookiecutter

RUN apt-get -y install npm
RUN apt-get clean

# Fix for R and libfortran
RUN ln -s /usr/lib/x86_64-linux-gnu/libgfortran.so.3 /usr/lib/libgfortran.so
RUN locale-gen en_US.UTF-8 en fi_FI.UTF-8

RUN mkdir /src

# INSTALL OpenMS
WORKDIR /src/
RUN git clone https://github.com/OpenMS/OpenMS.git /src/OpenMS-2.4.0
RUN git clone https://github.com/OpenMS/contrib.git
RUN mkdir contrib-build
WORKDIR /src/OpenMS-2.4.0
RUN git checkout Release2.4.0
WORKDIR /src/contrib-build
RUN cmake -DBUILD_TYPE=LIST ../contrib
RUN cmake -DBUILD_TYPE=ALL ../contrib
RUN mkdir -p /opt/OpenMS
WORKDIR /opt/OpenMS
RUN apt-get install -y qt5-default libeigen3-dev libwildmagic-dev libxerces-c-dev libboost-all-dev libsvn-dev libgsl-dev libbz2-dev
RUN apt-get install -y libqt5svg5 libqt5svg5-dev
RUN cmake -j20 -DCMAKE_PREFIX_PATH="/src/contrib-build;/usr/local" -DBOOST_USE_STATIC=OFF /src/OpenMS-2.4.0
RUN make -j20 OpenSwathWorkflow
RUN make -j20 OpenMS
RUN make -j20 TOPP
RUN make -j20 UTILS

# INSTALL PYPROPHET
RUN pip install numpy
RUN pip install matplotlib
RUN pip install numexpr
RUN pip install git+https://github.com/PyProphet/pyprophet.git@legacy

# INSTALL igcpep dependencies
RUN pip3 install biopython

# INSTALL TPP
RUN apt-get install -y libgd-dev
RUN mkdir -p /opt/tpp/
RUN mkdir /opt/tpp-data
WORKDIR /src/
RUN svn checkout svn://svn.code.sf.net/p/sashimi/code/tags/release_5-1-0
RUN echo "INSTALL_DIR = /opt/tpp\nBASE_URL = /tpp\nTPP_DATADIR = /opt/tpp-data" > release_5-1-0/site.mk
WORKDIR /src/release_5-1-0
COPY tpp-5.1-fix.diff /root/
COPY comet_source_2017014-fixed.zip extern/comet_source_2017014.zip
RUN wget https://sourceforge.net/projects/boost/files/boost/1.67.0/boost_1_67_0.tar.bz2 -P /src/release_5-1-0/extern/
RUN cat /root/tpp-5.1-fix.diff |patch -p0 
RUN make libgd
RUN mkdir -p build/gnu-x86_64/include/boost/nowide
RUN ln -s ../../../../extern/ProteoWizard/pwiz-src/libraries/boost_aux/boost/nowide build/gnu-x86_64/include/boost/nowide
RUN make all
RUN make install

# INSTALL msproteomicstools.git
RUN apt-get install -y cython cython3
RUN pip install msproteomicstools

# Install Comet
RUN mkdir -p /opt/comet
WORKDIR /opt/comet
RUN wget https://sourceforge.net/projects/comet-ms/files/comet_2017014.zip
RUN unzip comet_2017014.zip
RUN ln -s comet.2017014.linux.exe comet-ms
RUN chmod ugo+x comet.2017014.linux.exe

# Install tandem
WORKDIR /opt
RUN wget ftp://ftp.thegpm.org/projects/tandem/source/tandem-linux-17-02-01-4.zip
RUN unzip tandem-linux-17-02-01-4.zip
RUN mv tandem-linux-17-02-01-4 tandem
RUN ln -s /opt/tandem/bin/static_link_ubuntu/tandem.exe /opt/tandem/tandem
RUN chmod ugo+x /opt/tandem/bin/static_link_ubuntu/tandem.exe

# INSTALL msgfplus
RUN mkdir /opt/msgfplus
WORKDIR /opt/msgfplus
RUN wget https://github.com/MSGFPlus/msgfplus/releases/download/v2018.10.15/MSGFPlus_v20181015.zip
RUN unzip MSGFPlus_v20181015.zip

# INSTALL Percolator
WORKDIR /opt
RUN wget https://github.com/percolator/percolator/releases/download/rel-3-01/ubuntu64_release.tar.gz
RUN tar xfv ubuntu64_release.tar.gz
RUN dpkg -i percolator-converters-v3-01-linux-amd64.deb percolator-v3-01-linux-amd64.deb

# INSTALL luciphor2
RUN mkdir /opt/luciphor2
WORKDIR /opt/luciphor2
RUN wget https://sourceforge.net/projects/luciphor2/files/luciphor2.jar

# INSTALL dia-umpire
RUN mkdir /opt/dia-umpire
WORKDIR /opt/dia-umpire
RUN wget https://github.com/guoci/DIA-Umpire/releases/download/v2.1.3/v2.1.3.zip
RUN unzip v2.1.3.zip
RUN ln -s v2.1.3/DIA_Umpire_SE.jar DIA_Umpire_SE.jar

## Fetch diatools and install needed R-packages
RUN git clone https://github.com/elolab/diatools.git /opt/diatools
RUN mkdir /opt/diatools
COPY comet.params.template xtandem_settings.xml dia-pipeline.py install-R-packages.R iRTAssayLibrary.TraML iRT.txt diaumpire_params.txt swaths2stats.R /opt/diatools/
RUN mkdir /.Rcache
RUN chmod u+x /opt/diatools/install-R-packages.R
RUN /opt/diatools/install-R-packages.R

WORKDIR /

# Build image
# docker build -t diatools -f docker/Dockerfile .

