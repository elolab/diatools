#!/usr/bin/env Rscript

source("https://bioconductor.org/biocLite.R")
biocLite("SWATH2stats")
biocLite("PECA")
install.packages("tidyr",repos = "http://cran.us.r-project.org")
install.packages("argparse",repos = "http://cran.us.r-project.org")
install.packages("corrplot",repos = "http://cran.us.r-project.org")

