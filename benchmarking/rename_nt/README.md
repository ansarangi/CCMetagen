## Steps to rename the nt database to index with KMA

This script takes as input a sequential fasta file and a .tsv file with 2 headers: accession number and taxid.

You can download the accession2taxid map from NCBI with:
`wget ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz`


To extract the accession and the taxid info:
```
gunzip nucl_gb.accession2taxid.gz

cut -f 2-3 nucl_gb.accession2taxid > accession_taxid_nucl.map
```

Convert the genbank fasta file to sequencial fasta:
`awk '/^>/ {printf("\n%s\n",$0);next; } { printf("%s",$0);} END {printf("\n");}' < nt.fa > nt_sequential.fa`


