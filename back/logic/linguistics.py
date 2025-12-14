from mecab import MeCab
import pandas as pd
from itertools import chain
import random

def get_base_form(passage: str):
    target_pos = ['VA', 'VV', 'NNG', 'MAG', 'MAJ', 'MM']
    mecab = MeCab()
    parsed = mecab.parse(passage)
    df = pd.DataFrame([{
        'surface': m.surface,
        'pos': m.pos,
        'type': m.feature.type,
        'expression': m.feature.expression
    } for m in parsed])
    
    df['base'] = df['surface']
    inflect_mask = (df['type'] == 'Inflect') & df['expression'].notna()
    df.loc[inflect_mask, 'base'] = df.loc[inflect_mask, 'expression'].str.split('/').str[0]
    
    df['pos_tags'] = df['pos'].str.split('+')
    df['has_xsa'] = df['pos'].str.contains('XSA')
    df['has_xsv'] = df['pos'].str.contains('XSV')
    df['prev_surface'] = df['surface'].shift(1)
    
    xsa_mask = df['has_xsa'] & df['prev_surface'].notna()
    xsv_mask = df['has_xsv'] & df['prev_surface'].notna()
    
    df.loc[xsa_mask, 'combined'] = df.loc[xsa_mask, 'prev_surface'] + df.loc[xsa_mask, 'base'] + '다'
    df.loc[xsv_mask, 'combined'] = df.loc[xsv_mask, 'prev_surface'] + df.loc[xsv_mask, 'base'] + '다'
    
    xsa_xsv = (df['has_xsa'] | df['has_xsv']).astype(bool)
    df['next_has_xsa_xsv'] = xsa_xsv.shift(-1).astype(bool).fillna(False)
    df['prev_used'] = xsa_xsv.shift(1).astype(bool).fillna(False)
    
    va_results = df.loc[xsa_mask, ['combined']].assign(pos='VA').rename(columns={'combined': 'base'})
    vv_results = df.loc[xsv_mask, ['combined']].assign(pos='VV').rename(columns={'combined': 'base'})
    
    regular_mask = ~df['has_xsa'] & ~df['has_xsv'] & ~df['prev_used'] & ~df['next_has_xsa_xsv']
    regular_df = df.loc[regular_mask].explode('pos_tags')
    regular_results = regular_df[regular_df['pos_tags'].isin(target_pos)].groupby(level=0).first()[['base', 'pos_tags']].rename(columns={'pos_tags': 'pos'})
    
    va_vv_mask = regular_results['pos'].isin(['VA', 'VV'])
    regular_results.loc[va_vv_mask, 'base'] = regular_results.loc[va_vv_mask, 'base'] + '다'
    
    all_results = pd.concat([va_results, vv_results, regular_results]).reset_index(drop=True)
    counts = all_results.groupby(['base', 'pos']).size().reset_index(name='count')
    return list(zip(counts['base'], counts['pos'], counts['count']))
