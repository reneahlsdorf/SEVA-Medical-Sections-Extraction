import logging
import pandas as pd
import datetime

date_str = datetime.datetime.today().strftime('%Y-%m-%d')
logger = logging.getLogger(__name__)


def get_row_ids(client):
    """ Retrieve note texts from MIMIC with the given client object.

    Args:
        client: The BigQuery client

    Returns:
        list: The retrieved note ids
    """
    
    all_ids = """
    SELECT
        row_id
    FROM
        `physionet-data.mimiciii_notes.noteevents`
    """

    row_ids = client.query(all_ids).to_dataframe()
    row_ids = row_ids.row_id.unique()

    return row_ids


def get_note_texts(client, row_ids):
    """ Retrieve note texts from MIMIC with the given client object.

    Args:
        client: The BigQuery client
        row_ids (list): The list of integer row_ids to retrieve

    Returns:
        pd.DataFrame: The retrieved notes
    """
    
    sql = """
SELECT
    row_id, subject_id, hadm_id, chartdate, category, text 
FROM
    `physionet-data.mimiciii_notes.noteevents`
WHERE
    row_id in ({})
""".format(','.join([str(_) for _ in row_ids]))
    df = client.query(sql).to_dataframe()
    return df
