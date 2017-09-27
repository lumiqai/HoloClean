import os
import sys
import pandas as pd
import numpy as np
import sqlalchemy as sqla
import getpass
import logging
import dataset
sys.path.append('../')
from holoclean.utils import reader




class Dataengine:

    """Connects our program to the database

    """
    ################ Members ############
    
    
    
    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    def __init__(self,meta_filepath,data_filepath,dataset,index_name = None):
        logging.basicConfig(filename='dataengine.log', level=logging.DEBUG)
        self.data_filepath=data_filepath
        self.meta_filepath=meta_filepath
        self.dataset=dataset
        self.connect_metadb()
        self.connect_datadb()
        self.index_name=index_name
        
    
    def connect_datadb(self):
        """create a connection with the database"""
        dt_file = open(self.data_filepath,"r")
        
        # Connection part for the data 
        addressdt = dt_file.readline()
        dbnamedt = dt_file.readline()
        userdt = dt_file.readline()
        passworddt = dt_file.readline()
        
        
        con_str_data="mysql+mysqldb://" + userdt[:-1] +":"+passworddt[:-1]+"@"+addressdt[:-1]+"/"+dbnamedt[:-1]
        
        self.data_engine = sqla.create_engine(con_str_data)
        
        try:
            self.data_engine.connect()
            logging.info("Connection established to data database")      
        except:
            logging.warn("No connection to data database") 
     
            
    def connect_metadb(self):
        """create a connection with the database"""
        meta_file = open(self.meta_filepath,"r")
        
        
        # Connection part for the meta 
        addressmt = meta_file.readline()
        dbnamemt = meta_file.readline()
        usermt = meta_file.readline()
        passwordmt = meta_file.readline()
        1
        con_str_meta="mysql+mysqldb://" + usermt[:-1] +":"+passwordmt[:-1]+"@"+addressmt[:-1]+"/"+dbnamemt[:-1]
        

        self.meta_engine = sqla.create_engine(con_str_meta)
        
        try:
            self.meta_engine.connect() 
            logging.info("Connection established to meta data database")      
        except:
            logging.warn("No connection to meta database")
               

    def _csv2DB(self,table_name,chunk):
        """for the first chunk, create the table and return
        the name of the table"""

    	table_cols=chunk.columns
    	table_schema=''	
    	for i in table_cols:
    		table_schema=table_schema+","+str(i)
        table_schema=table_schema[1:]
    	self.add_meta(self.dataset.attributes[1], table_schema)
        
        """Add first table to data"""
        table_name_spc=self.dataset.spec_tb_name(table_name)
        try:
            chunk.to_sql(table_name_spc, con=self.data_engine, if_exists='append',
                         index=True, index_label=None)
            logging.info("Correct insertion for " + table_name_spc)
        except sqla.exc.IntegrityError:
            logging.warn("Failed to insert values")
            
        return table_name_spc
        
	
	def query(self, sql_query):
		return self.data_engine.execute(sql_query);
	
	def register(self, general_table_name, schema):
		schemaList = schema.split(",")
		q= "CREATE TABLE " + self.dataset.spec_tb_name(general_table_name)+ "("
		for i in schemaList:
			q = q + schemaList[i]+"TEXT,"
		schemaList = schemaList[:-1]
		q = q + ");"	

    def add(self, name_table , chunk = None):
        """adding the information from the chunk to the table"""
        try:
            chunk.to_sql(name_table, con=self.data_engine, if_exists='append',
                         index=True, index_label=None)
            logging.info("Correct insertion for " + name_table)
        except sqla.exc.IntegrityError:
            logging.warn("Failed to insert values")
 
    
    def retrieve(self,sql_query):
        

        if self.index_name is not None:
            generator = pd.read_sql_query(sql_query , self.data_engine )
        else:
            generator = pd.read_sql_query(sql_query , self.data_engine  )
        dataframe = pd.DataFrame(generator)
        
        if 'level_0'  in dataframe.columns:
            dataframe = dataframe.drop('level_0', 1)

        return dataframe
        		  
            
    def add_meta(self,table_name,table_schema):
        tmp_conn = self.meta_engine.raw_connection()
        dbcur=tmp_conn.cursor()
        stmt = "SHOW TABLES LIKE 'metatable'"
        dbcur.execute(stmt)
        result = dbcur.fetchone()
        add_row="INSERT INTO metatable (dataset_id,tablename,schem) VALUES('"+self.dataset.dataset_id+"','"+str(table_name)+"','"+str(table_schema)+"');"
        if result:
            # there is a table named "metatable"
            self.meta_engine.execute(add_row)              
        else:
            #create db with columns 'dataset_id' , 'tablename' , 'schem'
            # there are no tables named "metatable"
            create_table='CREATE TABLE metatable (dataset_id TEXT,tablename TEXT,schem TEXT);'
#             dbcur.execute(create_table)
            self.meta_engine.execute(create_table)
            self.meta_engine.execute(add_row)
            
            
    def get_schema(self,table_name):
        

        sql_query = "SELECT schem FROM metatable Where dataset_id = '"+self.dataset.dataset_id+"' AND  tablename = '"+table_name +"';"
        mt_eng=self.meta_engine
        
        generator = pd.read_sql_query(sql_query , mt_eng)
        dataframe = pd.DataFrame(generator)
        
        try :
            return dataframe.iloc[0][0]
        except:
            return "Not such element"


    def ingest(self,file_path):
        """
        This method creates an instance of the Reader class and write it to db
        
        """
                
        reader2db=reader.Reader(file_path) #Create Reader
        reader2db.reader(self)
        
    
    def get_table(self,table_name):
         
        table_get="Select * from "+self.dataset.table_name[self.dataset.attributes.index(table_name)]
        
        return self.retrieve(table_get)
        



# a=dataset.Dataset()
# print(a.setatrribute(1,"id"))
# d=dataengine("metadb-config.txt",'datadb-config.txt',a)
# print (d.register(chunk))
#print (  a.atrribute)         
#d=dataengine("metadb-config.txt")
#dataengine.connect_datadb('datadb-config.txt')
#d.add_meta("id_456", "T","index,attribute")
#print("Done!")

