import logging
import pandas as pd

logger = logging.getLogger(__name__)

def process_trigger_file(file_path):
    """Read in the trigger phrases and section groups file

    Args:
        file_path (str): Trigger file path

    """
    
    try:
        if file_path[-4:]=='.txt':
            trig_file = pd.read_csv(file_path, sep = '\t')
        elif file_path[-4:]=='.csv':
            trig_file = pd.read_csv(file_path)
        else:
            raise ValueError("Invalid file_path parameter")

        trig_file['section'] = [x.lower() for x in trig_file['section']]

        triggers = dict()
        groups = list(set(trig_file.section))

        groups.sort()
        for grp in groups:
            phrases = trig_file[trig_file.section == grp].match_phrase.tolist()
            triggers[grp] = phrases
        logger.debug("trigger keys '%s'", triggers.keys())

        phase_to_group = dict()
        for i in trig_file.index:
            phrase = trig_file.loc[i,'match_phrase'].replace('\\n','\n')
            group = trig_file.loc[i,'section']
            phase_to_group[phrase] = group
        logger.debug("phase_to_group key count: %d", len(phase_to_group.keys()))

        allphrases = trig_file.match_phrase.tolist()
        allphrases = [x.replace('\\n','\n') for x in allphrases]
        allphrases = sorted(allphrases, key=len, reverse = True)
        logger.debug("Count of all phrases: %d",len(allphrases))

        return triggers, phase_to_group, allphrases
    
    except Exception as e:
        print('Error reading or processing trigger file.')
        raise e
