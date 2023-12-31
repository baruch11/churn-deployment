import pandas as pd
import datetime
from chaos.infrastructure.connexion import Connexion
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, TIMESTAMP
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Historicize(Base):
    __tablename__ = 'historicize'

    ID = Column(Integer, primary_key=True)
    ID_CLIENT = Column(Integer)
    DATE_ENTREE = Column(Date)
    NOM = Column(String(70))
    PAYS = Column(String(50))
    SEXE = Column(String(10))
    AGE = Column(Integer)
    MEMBRE_ACTIF = Column(String(10))
    BALANCE = Column(Float)
    NB_PRODUITS = Column(Integer)
    CARTE_CREDIT = Column(String(10))
    SALAIRE = Column(Float)
    SCORE_CREDIT = Column(Float)
    CHURN = Column(Float)
    CALL_TIMESTAMP = Column(TIMESTAMP)


class CustomerLoader:

    def __init__(self):
        self.engine = Connexion().connect(sqlalchemy_engine=True)

    def find_a_customer(self, customer_id):
        """Query the database to find a customer

        Parameters
        ----------
        customer_id : int
                      client ID

        Returns
        -------
        raw_customer : pd.Dataframe
                       customer's features 

        """
        query = f"SELECT customer.ID_CLIENT, DATE_ENTREE, NOM, PAYS, SEXE, AGE,\
             MEMBRE_ACTIF, BALANCE, NB_PRODUITS, CARTE_CREDIT, \
                SALAIRE, SCORE_CREDIT, CHURN\
                FROM customer\
                INNER JOIN indicators ON \
                    customer.ID_CLIENT=indicators.ID_CLIENT\
                WHERE customer.ID_CLIENT = {customer_id};"
        raw_customer = pd.read_sql(query, self.engine)
        raw_customer.columns = raw_customer.columns.str.upper()
        return raw_customer

    def load_all_customer_raw(self):
        """Query the database to load complete data

        Returns
        -------
        data : pd.Dataframe
               complete data 

        """

        query = "SELECT customer.ID_CLIENT, DATE_ENTREE, NOM, PAYS, SEXE, AGE,\
             MEMBRE_ACTIF, BALANCE, NB_PRODUITS, CARTE_CREDIT, \
                SALAIRE, SCORE_CREDIT, CHURN\
                FROM customer\
                INNER JOIN indicators ON \
                    customer.ID_CLIENT=indicators.ID_CLIENT;"
        data = pd.read_sql(query, self.engine)
        return data
    
    def does_the_ID_exist(self, customer_id):
        """Query the database to find out if the id exists

        Parameters
        ----------
        customer_id : int
                      client ID
        Returns
        -------
        result_ : boolean

        """
        query = f"SELECT CASE \
             WHEN EXISTS(SELECT ID_CLIENT FROM customer WHERE ID_CLIENT = {customer_id}) \
                        THEN  'Client ID exists'\
                        ELSE  'Client ID does not exist' \
                        END AS result;"
        result_query = pd.read_sql(query, self.engine)
        result_ = result_query['result'].values.tolist()[0]
        return result_ == "Client ID exists"

    def historicize_api_calls(
            self,
            customer_input: dict,
            prediction: pd.Series) -> None:

        """ This function is used to store each prediction api calls into
        the table historicize. Those data could then be used by data drifting
        detectors to monitor and detect drift on data distribution.

         Parameters
        ----------
        customer_input : dict
                      customer data dict. 

        prediction : pd.Series
                        model prediction for the customer_input variable

        """
        current_time = datetime.datetime.now()
        historicize_dict = customer_input
        historicize_dict["ID"] = None
        historicize_dict["CHURN"] = prediction
        historicize_dict["CALL_TIMESTAMP"] = current_time
        historicize = Historicize(**historicize_dict)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        session.add(historicize)
        session.commit()
