import logging
import pandas as pd
import os, re
import time
import json
import datetime

date_str = datetime.datetime.today().strftime('%Y-%m-%d')
logger = logging.getLogger(__name__)


def spotter(text, phrase):
    start = text.find(phrase)
    if start >= 0:
        end = start + len(phrase)
        offsets = [start,end]
        return [phrase, offsets]
    else:
        return None

    
# Spot phrases with regex word boundaries, case insensitive
# Spots all occurrences for phrase in text
def spotter_multiple(text, phrase):
    """ Spot phrases with regex word boundaries, case insensitive
        Spots all occurrences for phrase in text

    Args:
        text (str): Text to search 
        phrase (str): Phrase to find

    Returns:
        list: [[begin_idx, end_idx]]
    """

    start = text.find(phrase)
    spots = []
    offset = 0
    while start >= 0:
        end = offset + start + len(phrase)
        offsets = [offset + start,end]
        spots.append([phrase, offsets])
        text = text[end:]
        offset += end
        start = text.find(phrase)
    if len(spots)==0:
        return None
    else:
        return spots

    
# Check submatches    
def check_submatch(offsets_curr, offsets_prior):
    """Check if prior offset fully included in current offset

    Args:
        offsets_curr (list): Current [begin_idx, end_idx] pair
        offsets_prior (list): Prior [begin_idx, end_idx] pair

    Returns:
        bool: Is prior fully included?
    """

    if (offsets_curr[0] > offsets_prior[0]) & (offsets_curr[1] < offsets_prior[1]):
        return True
    else:
        return False

    
def section_by_triggers(note, row_id, all_phrases, phrase_to_group):
    """Sectioning by trigger phrases

    Args:
        note (str): Full note text
        row_id (int): Row index
        all_phrases (list): All trigger phrases 
        phrase_to_group (dict): Mapping phrase to section group

    Returns:
        pd.DataFrame: DataFrame witgh extracted (not yet cleaned) sections.
    """

    start_to_spots = dict()
    end_to_spots = dict()

    if any(x in note for x in all_phrases):
        for phrase in all_phrases:
            spots = spotter_multiple(note, phrase)
            if spots != None:
                for spot in spots:
                    group = phrase_to_group[phrase]
                    start = spot[1][0]
                    end = spot[1][1]
                    spot.append(group)

                    add_current_end = True
                    # same start offset cases -- aiming for longest match
                    if start in start_to_spots.keys():
                        end_prior = start_to_spots[start][1][1]
                        if end > end_prior:
                            start_to_spots[start] = spot # else don't replace so get longest match
                            end_to_spots.pop(end_prior)
                        else:
                            add_current_end = False
                    else:
                        start_to_spots[start] = spot

                    # same end offset cases -- aiming for longest match
                    if end in end_to_spots.keys():
                        start_prior = end_to_spots[end][1][0]
                        if start < start_prior:
                            end_to_spots[end] = spot # else don't replace so get longest match 
                            start_to_spots.pop(start_prior)
                        else:
                            start_to_spots.pop(start)
                    elif add_current_end:
                        end_to_spots[end] = spot

    df_section = {
        "row_id": [],
        "extracted_section_title": [],
        "section_group": [],
        "section_text": [], 
        "start": [],
        "end": [],}
    start_prior = 0
    end_prior = 0
    count = 0
    start_offsets = sorted(start_to_spots.keys())
        
    for i in range(len(start_offsets)):
        start = start_offsets[i]
        spot = start_to_spots[start]
        if i != 0:
            offsets_curr = spot[1]
            spot_prior = start_to_spots[start_offsets[i-1]]
            offsets_prior = spot_prior[1]
            submatch = check_submatch(offsets_curr, offsets_prior)
        else:
            submatch = False

        if submatch == False:
            phrase = spot[0]
            startcurrent = spot[1][0]
            endcurrent = spot[1][1]
            group = spot[2]

            # for the section text before the first detectable section phrase:
            if (start_prior == 0)&(startcurrent!=0)&(count==0):
                df_section['row_id'].append(row_id)
                df_section['extracted_section_title'].append('')
                df_section['section_group'].append('')
                df_section['start'].append(0)
                df_section['end'].append(startcurrent)
                df_section['section_text'].append(note[:startcurrent])

            # for the first detected section phrase and after
            df_section['row_id'].append(row_id)
            df_section['extracted_section_title'].append(phrase)
            df_section['section_group'].append(group)
            df_section['start'].append(endcurrent)

            # append end offset and section text to prior section in next iteration
            if count > 0: 
                df_section['end'].append(startcurrent)
                df_section['section_text'].append(note[end_prior:startcurrent])
            start_prior = startcurrent
            end_prior = endcurrent
            count = count + 1
    
    # append end offset and section text to the last section
    if len(df_section['row_id'])>0:
        df_section['end'].append(len(note))
        df_section['section_text'].append(note[end_prior:])
    
    df_section = pd.DataFrame(df_section).copy()
    df_section['index'] = df_section.index
    df_section['section_id'] = [str(idx) + '|' + str(rowid) + '.txt' for idx, rowid in zip(df_section['index'], df_section['row_id'])]

    return df_section


def group_contiguous_sections(df_sectioned, note):
    """Grouping group contiguous sections to larger section groups

    Args:
        df_sectioned (pd.DataDrame): Dataframe with sections
        note (str): The full note text

    Returns:
        pd.DataFrame: DataFrame with extracted and cleaned sections.
    """

    df = df_sectioned.copy()
    sectionidprior = df.loc[0,'section_id']
    grpprior = df.loc[0,'section_group']
    start = df.loc[0,'start']
    end = df.loc[0,'end']
    df_grouped = {
        "row_id": [],
        "extracted_section_title": [],
        "section_group": [],
        "section_text": [],
        "start": [],
        "end": [],
        'index': [],
        'section_id': [],}

    phrases = []
    last_index = df.index.tolist()[-1]

    for i in df.index:
        sectionidcurr = df.loc[i,'section_id']
        grpcurr = df.loc[i,'section_group']
        if grpcurr == grpprior:
            phrase = df.loc[i,'extracted_section_title']
            phrases.append(phrase)
            end = df.loc[i,'end'] # updates end offset   
        else:
            # append prior section texts
            row_id = sectionidprior.split('|')[1].replace('.txt','')
            idx = sectionidprior.split('|')[0]

            df_grouped['row_id'].append(row_id)
            df_grouped['extracted_section_title'].append(phrases[0]) #first section title text kept
            df_grouped['section_group'].append(grpprior)

            text = note[start:end]

            df_grouped['section_text'].append(text)
            df_grouped['start'].append(start)  
            df_grouped['end'].append(end) 
            df_grouped['index'].append(idx)  
            df_grouped['section_id'].append(sectionidprior)

            # updates offsets for current section
            sectionidprior = sectionidcurr
            grpprior = grpcurr
            start = df.loc[i,'start']
            end = df.loc[i,'end']
            phrases = [df.loc[i,'extracted_section_title']]

        if i == last_index:
            # append prior section texts
            row_id = sectionidprior.split('|')[1].replace('.txt','')
            idx = sectionidprior.split('|')[0]

            df_grouped['row_id'].append(row_id)
            df_grouped['extracted_section_title'].append(phrases[0]) #first section title text kept
            df_grouped['section_group'].append(grpprior)

            text = note[start:end]

            df_grouped['section_text'].append(text)
            df_grouped['start'].append(start)  
            df_grouped['end'].append(end) 
            df_grouped['index'].append(idx)  
            df_grouped['section_id'].append(sectionidprior)

    df_grouped = pd.DataFrame(df_grouped)
    return df_grouped


# Section notes
def section_notes(notes, note_ids, missed, all_phrases, phrase_to_group, export_path = None): 
    """_summary_

    Args:
        notes (list): List with all note texts
        note_ids (list): List with all note ids
        missed (list): List which will be filled with all errorneous note ids
        all_phrases (list): List with all phrases for section identification
        phrase_to_group (_type_): Mapping of phrase headers to section groups
        export_path (_type_, optional): If set, the path to which to save the sections (in txt files) to. Defaults to None.

    Returns:
        tuple: [DataFrame with all notes, list with notes that included mistakes]
    """

    df_notes = pd.DataFrame(
        {"row_id": [],
        "extracted_section_title": [],
        "section_group": [],
        "section_text": [],
        "start": [],
        "end": [],
        'index': [],
        'section_id':[]})

    count = 0
    for note, note_id in zip(notes, note_ids):
        if count % 1000 ==0 and count > 0:
            logger.info('Sectioned ', count, ' notes')
        count = count + 1
        try:
            note = note.split("\n")
            note = [_.lstrip() for _ in note]
            note = "\n".join(note)
            df_sectioned = section_by_triggers(note, note_id, all_phrases, phrase_to_group)

            if df_sectioned.shape[0] == 0:
                missed.append(note_id)
            else:
                df_section_grouped = group_contiguous_sections(df_sectioned, note)
                df_notes = df_notes.append(df_section_grouped, ignore_index=True)
        except Exception as e:
            logger.warn('Failed to section: %s', note_id)
            missed.append(note_id)
            raise e

    logger.info('Done: %d sections', df_notes.shape)
    
    if export_path != None:
        logger.info('Exporting sectioned results')
        
        df_notes.to_csv(os.path.join(export_path, 'sectioned_' + str(len(set(df_notes.row_id))) + '_notes_' + date_str + '.txt')
                       , sep='\t', encoding='utf-8', index=False)
        
        with open(os.path.join(export_path,'missed_notes_' + date_str + '.txt'), 'w') as f:
            for id in missed:
                f.write(str(id) + '\n')
        
    return df_notes, missed

