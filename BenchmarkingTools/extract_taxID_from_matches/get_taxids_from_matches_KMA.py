#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parse the results of 1 KMA res file and store them in the SQLite3 'bench.db'
Works for ITS, RefSeq and UniProt, get their taxids and lineages (as identified in the Ref Database)
@ V.R.Marcelino
Created on Tue Jul 10 17:12:08 2018
"""

import csv
import re
from argparse import ArgumentParser
import sqlite3
from ete3 import NCBITaxa
ncbi = NCBITaxa()

parser = ArgumentParser()
parser.add_argument('-i', '--input_kma_result', help='The path to the .res or .spa file', required=True)
parser.add_argument('-n', '--input_sample_name', help='Tthe name of the sample', required=True)
parser.add_argument('-r', '--reference_database', help='Reference database used, options are ITS, RefSeq, UniProt and nt', required=True)
parser.add_argument('-sql', '--SQL_db', help='SQL database where it should store the data', required=True)

args = parser.parse_args()
in_res_file = args.input_kma_result
ref_database = args.reference_database
sql_fp = args.SQL_db
sample_name = args.input_sample_name


# Tests and torubleshooting
ref_database = "ITS" # options are ITS, RefSeq or UniProt
in_res_file = "2_mtg_ITS.res"
#in_res_file_RefSeq = "2_mtg_refSeq_bf.spa"
sql_fp="benchm.db"
sample_name="mtg"

############# 
connection = sqlite3.connect(sql_fp)
cursor = connection.cursor()

# Create a table if it does not exist:
query = "CREATE TABLE IF NOT EXISTS KMA (TaxID integer, Lineage text, Sample text, RefDatabase text, Abundance text);"
cursor.execute(query)
connection.commit()

############# 

### class that stores taxid and other info # script 1
class tax_info_from_match(): 
    
    def __init__(self, TaxId=None, Lineage=None, Sample=None, RefDatabase=None, 
                 Abundance=None):
        
        # info from matches
        self.TaxId = TaxId
        self.Lineage = Lineage
        self.Sample = Sample
        self.RefDatabase = RefDatabase
        self.Abundance = Abundance



### class that stores lineage in ranks using NCBI taxa # script 1
class tax_info_from_ncbi(): 
    
    def __init__(self, Kingdom=None, Kingdom_TaxId=None, Phylum=None, 
                 Phylum_TaxId=None, Class=None, Class_TaxId=None,
                 Order=None, Order_TaxId=None, Family=None, Family_TaxId=None,
                 Genus=None, Genus_TaxId=None, Species=None, Species_TaxId=None):

        # info from NCBI
        self.Kingdom = Kingdom
        self.Kingdom_TaxId = Kingdom_TaxId
        self.Phylum = Phylum
        self.Phylum_TaxId = Phylum_TaxId
        self.Class = Class
        self.Class_TaxId = Class_TaxId
        self.Order = Order
        self.Order_TaxId = Order_TaxId
        self.Genus = Genus
        self.Genus_TaxId = Genus_TaxId
        self.Species = Species
        self.Species_TaxId = Species_TaxId



### function that takes taxid and returns all the lineage info # script 2
def lineage_extractor(query_taxid):
    list_of_taxa_ranks = ['kingdom', 'phylum', 'class', 'order', 'family','genus', 'species']
    lineage = ncbi.get_lineage(query_taxid)
    ranks = ncbi.get_rank(lineage)
    names = ncbi.get_taxid_translator(lineage)

    tax_info = tax_info_from_ncbi()

    for key, val in ranks.items():
        if val == list_of_taxa_ranks[0]:
            tax_info.Kingdom = names[key]
            tax_info.Kingdom_TaxId = key
            
        elif val == list_of_taxa_ranks[1]:
            tax_info.Phylum = names[key]
            tax_info.Phylum_TaxId = key
            
        elif val == list_of_taxa_ranks[2]:
            tax_info.Class = names[key]
            tax_info.Class_TaxId = key
            
        elif val == list_of_taxa_ranks[3]:
            tax_info.Order = names[key]
            tax_info.Order_TaxId = key
        
        elif val == list_of_taxa_ranks[4]:
            tax_info.Class = names[key]
            tax_info.Class_TaxId = key
            
        elif val == list_of_taxa_ranks[5]:
            tax_info.Genus = names[key]
            tax_info.Genus_TaxId = key
            
        elif val == list_of_taxa_ranks[6]:
            tax_info.Species = names[key]
            tax_info.Species_TaxId = key
    return tax_info


#x = lineage_extractor(125858)


# Read and store taxids in list of classes
store_lineage_info = []

# function with the following inputs
# in_res_file, sample, database,

with open(in_res_file) as res:
    next (res) # skip first line
    for line in csv.reader(res, delimiter='\t'):      
        split_match = re.split (r'(\|| )', line[0])

        match_info = tax_info_from_match()
        
        if ref_database == "ITS":
            
            if split_match[4] != 'unk_taxid':
                match_info.TaxId = split_match[4]
                match_info.Lineage = split_match[12]
            
            # Handle unknown taxids: 
            else:
                full_lin = split_match[12]
                species_full_name = full_lin.split('_')[-2:]
                species_name_part2 = species_full_name[1].replace('sp', 'sp.')
                species_name = species_full_name[0] + " " + species_name_part2
                
                # get taxid from species name
                retrieved_taxid = ncbi.get_name_translator([species_name])
                
                # if unkwnon, try with genus only:
                if len(retrieved_taxid) == 0:
                    retrieved_taxid = ncbi.get_name_translator([species_full_name[0]])
                
                    # if still not found, print warning
                    if len(retrieved_taxid) == 0:
                        print ("")
                        print ("WARNING: no taxid found for %s" %(full_lin))
                        print ("this match will not be included in the comparisons")
                        print ("")

        elif ref_database == "RefSeq":
            match_info.TaxId = split_match[4]
            species = split_match[6] + " " + split_match[8]
            match_info.Lineage = species
        
        elif ref_database == "UniProt":
            print("write something to search after TaxID=")
            
        elif ref_database == "nt":
            print("write something to search for taxid based on species name")
            
        else:
            print ("ref_database must be ITS, RefSeq, UniProt or nt")

        
        Abund = line[-3].split(' ')[-1] # Raw 'Depth' value
        match_info.Abundance = Abund
        match_info.Sample = sample_name
        match_info.RefDatabase = ref_database
        store_lineage_info.append(match_info)


# output as a SQLite3:
query = "INSERT INTO KMA VALUES (?,?,?,?,?);"
for i in store_lineage_info:
    cursor.execute(query,(i.TaxId, i.Lineage, i.Sample, i.RefDatabase, i.Abundance))
    
# Save db    
connection.commit()
connection.close()

#################
#check it is all right
for i in store_lineage_info:
    print (i.TaxId)
    print (i.Lineage)
    print (i.Sample)
    print (i.RefDatabase)
    print (i.Abundance)


for i in store_lineage_info:
    if i.TaxId == 'unk_taxid':
        print (i.TaxId)
        print (i.Lineage)
        
        

cursor.execute("SELECT * FROM KMA;")
cursor.fetchall()






