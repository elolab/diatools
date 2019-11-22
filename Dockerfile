FROM ubuntu:17.04

MAINTAINER Sami

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y apt-utils

RUN apt-get update \
    && apt-get install -y wget\
    && apt-get install -y python-pip\
    && apt-get install -y python3-pip\
    && apt-get install -y git\
    && apt-get install -y emacs-nox\
    && apt-get install -y build-essential\
    && apt-get build-dep -y openms\	
    && apt-get -y install openssh-server\
    && apt-get -y install sshfs\
    && apt-get -y install tandem-mass\
    && apt-get -y install openjdk-8-jdk\
    && apt-get -y install screen\
    && apt-get -y install xpra\
    && apt-get -y install g++\
    && apt-get -y install g++-4.9\
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
    && apt-get -y install sudo\
    && apt-get -y install r-base\
    && apt-get -y install r-base-dev\
    && apt-get -y install r-cran-data.table\
    && apt-get -y install r-bioc-biobase\
    && apt-get -y install r-bioc-biocgenerics\
    && apt-get -y install r-bioc-deseq2\
    && apt-get -y install r-cran-randomforest\
    && apt-get -y install r-cran-mvtnorm\
    && apt-get -y install r-bioc-biocinstaller\
    && apt-get -y install r-cran-ade4\
    && apt-get -y install r-cran-minqa\
    && apt-get -y install gfortran-multilib\
    && apt-get -y install python3-pandas \
    && apt-get -y install python3-pandas-lib \
    && apt-get -y install cmake

#RUN dpkg --add-architecture i386\
#    && apt-get update\
#    && apt-get -y install wine32

RUN apt-get clean

# Fix for R and libfortran
RUN ln -s /usr/lib/x86_64-linux-gnu/libgfortran.so.3 /usr/lib/libgfortran.so

RUN echo 'root:Ymko7WFcLfe4U' | chpasswd
#RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
#RUN sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN mkdir /var/run/sshd

RUN locale-gen en_US.UTF-8 en fi_FI.UTF-8

RUN mkdir /src
WORKDIR /src/

# INSTALL OpenMS
RUN git clone https://github.com/OpenMS/OpenMS.git /src/OpenMS-git
RUN git clone https://github.com/OpenMS/contrib.git
RUN mkdir contrib-build
WORKDIR /src/contrib-build
RUN cmake -DBUILD_TYPE=LIST ../contrib
RUN cmake -DBUILD_TYPE=ALL ../contrib
RUN mkdir -p /opt/OpenMS
WORKDIR /opt/OpenMS
RUN cmake -j20 -DCMAKE_PREFIX_PATH="/src/contrib-build;/usr/local" -DBOOST_USE_STATIC=OFF /src/OpenMS-git
RUN make -j20 OpenSwathWorkflow
RUN make -j20 OpenMS
RUN make -j20 TOPP
RUN make -j20 UTILS

# INSTALL PYPROPHER
RUN easy_install -U distribute
RUN pip install numpy
RUN pip install matplotlib
RUN pip install numexpr
RUN pip install pyprophet

# INSTALL TPP
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-6 10
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.9 20
RUN update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-6 10
RUN update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.9 20
RUN mkdir -p /opt/tpp/
RUN mkdir /opt/tpp-data
WORKDIR /src
RUN wget https://downloads.sourceforge.net/project/sashimi/Trans-Proteomic%20Pipeline%20%28TPP%29/TPP%20v5.0%20%28Typhoon%29%20rev%200/TPP_5.0.0-src.tgz
RUN tar xfv TPP_5.0.0-src.tgz
RUN echo "INSTALL_DIR = /opt/tpp\nBASE_URL = /tpp\nTPP_DATADIR = /opt/tpp-data" > TPP_5.0.0-src/site.mk
#RUN cat tpp-svn/site.mk
WORKDIR /src/TPP_5.0.0-src
RUN mkdir -p ./extern/ProteoWizard/pwiz-msi
RUN make pwiz-msi; exit 0
RUN sed -i 's/ /./g' ./extern/ProteoWizard/pwiz-msi/VERSION
RUN sed -i 's/rm -f $(PWIZ_MSIDIR)\/VERSION/#/g' ./extern/ProteoWizard/Makefile
RUN sed -i 's/wget -nv -O $(PWIZ_MSIDIR)\/VERSION $(PWIZ_TCMSI)\/VERSION\\?guest=1/#/g' ./extern/ProteoWizard/Makefile
RUN make pwiz-msi
RUN make libgd
RUN make all
#RUN cat perl/Makefile |grep -v plotxy > perl/Makefile; exit 0
RUN make install

# INSTALL msproteomicstools.git
RUN pip install msproteomicstools

# Install Comet
RUN mkdir -p /opt/comet
WORKDIR /opt/comet
RUN wget https://downloads.sourceforge.net/project/comet-ms/comet_binaries_2016010.zip
RUN unzip comet_binaries_2016010.zip
RUN ln -s comet_binaries_2016010/comet.2016010.linux.exe comet-ms
RUN chmod ugo+x comet_binaries_2016010/comet.2016010.linux.exe

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
RUN wget https://omics.pnl.gov/sites/default/files/MSGFPlus.zip
RUN unzip MSGFPlus.zip

# INSTALL Percolator
WORKDIR /opt
RUN wget https://github.com/percolator/percolator/releases/download/rel-3-01/ubuntu64_release.tar.gz
RUN tar xfv ubuntu64_release.tar.gz
RUN dpkg -i percolator-converters-v3-01-linux-amd64.deb percolator-v3-01-linux-amd64.deb

#RUN python3 -m pip install pymzML

WORKDIR /workdir

RUN mkdir /.Rcache



