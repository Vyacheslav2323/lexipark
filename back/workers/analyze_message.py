from back.database.db import SessionLocal 
from back.database.models import Message, Vocab, User_Vocab, Chat, VocabOccurrence, Grammar, User_Grammar, GrammarOccurrence 
from back.logic.linguistics import get_base_form 
from uuid import UUID 
import re 
from typing import Optional, Dict 

def analyze_message(message_id: UUID): 
    db = SessionLocal() 
    msg = db.query(Message).get(message_id) 
    if not msg: 
        return 
    chat = db.query(Chat).get(msg.chat_id) 
    if msg.text and not msg.text.startswith("PATTERN: "):
        vocab_results = get_base_form(msg.text) 
        persist_vocab_results( db = db, user_id = chat.user_id, vocab_results = vocab_results, message_id = message_id ) 
    persist_grammar_results( db = db, user_id = chat.user_id, text = msg.text, message_id = message_id ) 
    db.commit() 

def persist_vocab_results(db, user_id, vocab_results, message_id): 
    for base, pos, count in vocab_results: 
        vocab = ( 
            db.query(Vocab) 
            .filter(Vocab.base == base, Vocab.pos == pos) 
            .first() ) 
        if not vocab: 
            vocab = Vocab( 
                base=base, 
                pos=pos, 
                count=count, 
                message_id=message_id 
            ) 
            db.add(vocab) 
            db.flush()
        else: 
            vocab.count += count 

        user_vocab = ( 
            db.query(User_Vocab) 
            .filter( 
                User_Vocab.user_id == user_id, 
                User_Vocab.vocab_id == vocab.id ) 
            .first() 
            ) 
        if not user_vocab: 
            user_vocab = User_Vocab( 
                user_id=user_id, 
                vocab_id=vocab.id, 
                count=count 
            ) 
            db.add(user_vocab) 
        else: 
            user_vocab.count += count 

        vocab_occurrence = VocabOccurrence( 
            vocab_id=vocab.id, 
            message_id=message_id 
        ) 
        db.add(vocab_occurrence) 
        
FIELDS = [ 'PATTERN', 'FUNCTION', 'MEANING', 'BOUNDARY' ] 

def parse_lesson(text: str) -> Optional[Dict[str, str]]: 
    result = {} 
    for field in FIELDS: 
        m = re.search( 
            rf"{field}:\s*(.*?)(?=\n(?:{'|'.join(FIELDS)}):|\Z)", 
            text, 
            flags=re.S 
        ) 
        result[field.lower()] = m.group(1).strip() if m else "" 
    if not result['pattern']: 
        return None
    return result 
    
def persist_grammar_results(db, user_id, text, message_id): 
    lesson = parse_lesson(text) 
    if not lesson: 
        return 
    grammar = db.query(Grammar).filter(Grammar.title == lesson['pattern']).first() 
    if not grammar: 
        grammar = Grammar( 
            title=lesson['pattern'], 
            function=lesson['function'], 
            meaning=lesson['meaning'], 
            boundary=lesson['boundary'] 
        ) 
        db.add(grammar) 
    else: 
        grammar.count += 1 
    
    user_grammar = db.query(User_Grammar).filter( 
        User_Grammar.user_id == user_id, 
        User_Grammar.grammar_id == grammar.id 
    ).first() 
    if not user_grammar: 
        user_grammar = User_Grammar( 
            user_id=user_id, 
            grammar_id=grammar.id, 
            count=1 ) 
        db.add(user_grammar) 
        
    grammar_occurrence = GrammarOccurrence( 
        grammar_id=grammar.id, 
        message_id=message_id 
    ) 
    db.add(grammar_occurrence)