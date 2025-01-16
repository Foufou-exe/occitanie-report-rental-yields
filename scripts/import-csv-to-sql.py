import pandas as pd
import numpy as np
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, VARCHAR
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()
    
class RentalYield(Base):
    """
    RentalYield class represents the rental yield data for communes.

    Attributes:
        id (str): Primary key, unique identifier for the rental yield record.
        insee_com (str): INSEE code for the commune.
        insee_dep (str): INSEE code for the department.
        insee_reg (str): INSEE code for the region.
        nom_commune (str): Name of the commune.
        population (int): Population of the commune.
        nb_ventes (int): Number of sales in the commune.
        prix_moyen_m2 (int): Average price per square meter in the commune.
        prix_loyer_m2_maison (float): Average rental price per square meter for houses in the commune.
        prix_loyer_m2_appart (float): Average rental price per square meter for apartments in the commune.
        rendement_locatif_appart_m2 (float): Rental yield per square meter for apartments in the commune.
        rendement_locatif_maison_m2 (float): Rental yield per square meter for houses in the commune.
    """
    __tablename__ = 'rendement_locatif_communes'
    id = Column(String(255), primary_key=True)
    insee_com = Column(String(255), nullable=True)
    insee_dep = Column(String(255), nullable=True)
    insee_reg = Column(String(255), nullable=True)
    nom_commune = Column(String(255), nullable=True)
    population = Column(Integer, nullable=True)
    nb_ventes = Column(Integer, nullable=True)
    prix_moyen_m2 = Column(Integer, nullable=True)
    prix_loyer_m2_maison= Column(Float, nullable=True)
    prix_loyer_m2_appart = Column(Float, nullable=True)
    rendement_locatif_appart_m2 = Column(Float, nullable=True)
    rendement_locatif_maison_m2 = Column(Float, nullable=True)

class LifeLevel(Base):
    """
    Represents the life level data for communes.

    Attributes:
        insee_com (str): The INSEE code of the commune, serves as the primary key.
        life_level (int, optional): The life level of the commune.
    """
    __tablename__ = 'niveau_vie_communes'
    insee_com = Column(String(255), primary_key=True)
    life_level = Column(Integer, nullable=True)


class DataReader:
    """A class used to read data from CSV and Excel files.
    Attributes:
    ----------
    file : str
        The path to the file to be read.
    Methods:
    -------
    read_data_csv(separator: str) -> pd.DataFrame:
        Reads data from a CSV file and returns it as a DataFrame.
    read_data_excel(sheet_name: str) -> pd.DataFrame:
        Reads data from an Excel file and returns it as a DataFrame.
    """
    def __init__(self, file):
        self.file = file

    def read_data_csv(self, separator: str) -> pd.DataFrame:
        """Reads data from a CSV file

        Returns:
            pd.DataFrame: Dataframe with raw data
        """
        logging.info("Reading CSV file...")
        return pd.read_csv(self.file, sep=separator, na_values="NA")
    
    def read_data_excel(self, sheet_name: str) -> pd.DataFrame:
        """Reads data from an Excel file

        Returns:
            pd.DataFrame: Dataframe with raw data
        """
        logging.info("Reading Excel file...")
        return pd.read_excel(self.file, sheet_name=sheet_name, na_values="nan")

class DataTransformer:
    @staticmethod
    def transform_data_rental_yield(data: pd.DataFrame) -> pd.DataFrame:
        """Transforms raw data

        Args:
            data (pd.DataFrame): Raw data

        Returns:
            pd.DataFrame: Transformed data
        """
        logging.info("Transforming data...")
        # If the column 'INSEE_COM' has less than 5 characters, we fill it with zeros at the beginning
        data['INSEE_COM'] = data['INSEE_COM'].astype(str).str.zfill(5)
        # If the column 'INSEE_DEP' has less than 2 characters, we fill it with zeros at the beginning
        data['INSEE_DEP'] = data['INSEE_DEP'].astype(str).str.zfill(2)
        # Create a new calculated column 'RENDEMENT_LOCATIF_APPART_M2'
        data['RENDEMENT_LOCATIF_APPART_M2'] = np.where(
            data['PrixMoyen_M2'] != 0,
            ((data['loyer_apparts'] * 12) / data['PrixMoyen_M2']) * 100,
            0
        )
        # Create a new calculated column 'RENDEMENT_LOCATIF_MAISON_M2
        data['RENDEMENT_LOCATIF_MAISON_M2'] = np.where(
            data['PrixMoyen_M2'] != 0,
            ((data['loyer_maisons'] * 12) / data['PrixMoyen_M2']) * 100,
            0
        )
        # Round column 'RENDEMENT_LOCATIF_APPART_M2' to 2 decimal places
        data['RENDEMENT_LOCATIF_APPART_M2'] = data['RENDEMENT_LOCATIF_APPART_M2'].round(2)
        # Round column 'RENDEMENT_LOCATIF_MAISON_M2' to 2 decimal places
        data['RENDEMENT_LOCATIF_MAISON_M2'] = data['RENDEMENT_LOCATIF_MAISON_M2'].round(2)
        # Round column 'loyer_maisons' to 2 decimal places
        data['loyer_maisons'] = data['loyer_maisons'].round(2)
        # Round column 'loyer_apparts' to 2 decimal places
        data['loyer_apparts'] = data['loyer_apparts'].round(2)
        return data
    
    @staticmethod
    def transform_data_life_level(data: pd.DataFrame) -> pd.DataFrame:
        """Transforms raw data

        Args:
            data (pd.DataFrame): Raw data

        Returns:
            pd.DataFrame: Transformed data
        """
        logging.info("Transforming data...")
        data = data.drop_duplicates(subset=['Code Commune'], keep='first')
        data['Niveau de vie Commune'] = data['Niveau de vie Commune'].fillna(0)
        return data

class DatabaseHandler:
    def __init__(self, db_uri):
        self.db_uri = db_uri
        self.engine = create_engine(db_uri)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Creates tables in the database
        """
        logging.info("Creating tables in the database...")
        Base.metadata.create_all(self.engine)

    def insert_data_rental_yield(self, data: pd.DataFrame) -> None:
        """Inserts data into the database

        Args:
            data (pd.DataFrame): Data to insert into the database
        """
        logging.info("Inserting data into the database...")
        session = self.Session()
        for _, row in data.iterrows():
            rental_yield_commune = RentalYield(
                id=row['ID'],
                insee_com=row['INSEE_COM'],
                insee_dep=row['INSEE_DEP'],
                insee_reg=row['INSEE_REG'],
                nom_commune=row['NOM_COM_M'],
                population=row['POPULATION'],
                nb_ventes=row['Nb_Ventes'],
                prix_moyen_m2=row['PrixMoyen_M2'],
                prix_loyer_m2_maison=row['loyer_maisons'],
                prix_loyer_m2_appart=row['loyer_apparts'],
                rendement_locatif_appart_m2=row['RENDEMENT_LOCATIF_APPART_M2'],
                rendement_locatif_maison_m2=row['RENDEMENT_LOCATIF_MAISON_M2'],
            )
            session.add(rental_yield_commune)
        session.commit()
        session.close()
        
    def insert_data_life_level(self, data: pd.DataFrame) -> None:
        """Inserts data into the database

        Args:
            data (pd.DataFrame): Data to insert into the database
        """
        logging.info("Inserting data into the database...")
        session = self.Session()
        for _, row in data.iterrows():
            life_level_commune = LifeLevel(
                insee_com=row['Code Commune'],
                life_level=row['Niveau de vie Commune']
            )
            session.add(life_level_commune)
        session.commit()
        session.close()

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # Define file paths
    csv_file_rental_yield = '../sources/original/prixm2-loyer-communes-2019.csv'
    excel_file_life_level = '../sources/original/niveau-vie-communes.xlsx'
    # Define database URI
    db_uri = 'mysql://root:@localhost/jasper_report_rental_yield'

    #  Read data from CSV file 
    data_reader_rental_yield = DataReader(csv_file_rental_yield)
    raw_data_rental_yield = data_reader_rental_yield.read_data_csv(separator=',')
    
    data_reader_life_level = DataReader(excel_file_life_level)
    raw_data_life_level = data_reader_life_level.read_data_excel(sheet_name='Data')

    # Transform data
    transformed_data_rental_yield = DataTransformer.transform_data_rental_yield(raw_data_rental_yield)
    transformed_data_life_level = DataTransformer.transform_data_life_level(raw_data_life_level)

    # Insert data into the database
    db_handler = DatabaseHandler(db_uri)
    db_handler.create_tables()
    db_handler.insert_data_rental_yield(transformed_data_rental_yield)
    db_handler.insert_data_life_level(transformed_data_life_level)

if __name__ == "__main__":
    main()
    
