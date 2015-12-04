import re
import os
from collections import Counter
import json
import numpy as np

alphabet = re.compile('[a-zA-Z0-9-]+|[,.?!:;]')
UNIQUE_WORD = '#$&'
ENDS_OF_SENTENCES = ['.', '!', '?']
PUNCTUATION = ENDS_OF_SENTENCES + [',',';', ':']

AFTER_WORDS = ['t', 'll', 's', 've', 're', 'm', 'd']
ABBREVIATIONS = ['mr', 'mrs', 'ms', 'dr', 'prof', 'st', 'rd',
                'jan', 'feb', 'apr', 'aug', 'sept', 'oct', 'nov', 'dec',
                'mon', 'tues', 'wed', 'thurs', 'fri', 'sat', 'sun']

QUESTION_WORDS = ['do', 'did', 'does', 'have', 'has', 'could', 'may', 'should', 
                  'can', 'must', 'shall', 'would',
                  'am', 'is', 'are', 'will', 'was',
                  'when', 'where', 'what', 'why', 'how', 'which', 'who', 
                  'whose', 'whom']

def convert_to_list_of_lexems(file_name):
    lexems = []
    text = open(file_name)
    for line in text:
        line = clean_line(line)
        for lexem in alphabet.findall(line):
            if lexem.lower() in AFTER_WORDS:
                lexem = "\'" + lexem
            lexems.append(lexem)
    return lexems

def clean_line(line):
    line = line.replace('...', '.').replace('..', '.');
    line = line.replace('-', ' ').replace('  ', ' ');
    line = line.translate(None, '"#%^&-*()@$%[]{}><') 
    return line

def update_counters(lexems, two_words_counter, three_words_counter):
    first_word = UNIQUE_WORD
    second_word = UNIQUE_WORD
    for third_word in lexems:
        insert_to_counters((first_word, second_word, third_word), 
                           two_words_counter, three_words_counter)
        if (third_word in ENDS_OF_SENTENCES and second_word.lower() not in 
                ABBREVIATIONS and (len(second_word) > 2)): 
            insert_to_counters((second_word, third_word, UNIQUE_WORD),
                               two_words_counter, three_words_counter)
            insert_to_counters((third_word, UNIQUE_WORD, UNIQUE_WORD), 
                               two_words_counter, three_words_counter)
            first_word = UNIQUE_WORD
            second_word = UNIQUE_WORD
        else:
            first_word, second_word = second_word, third_word

def insert_to_counters(triple, two_words_counter, three_words_counter):
    two_words_counter[(triple[0], triple[1])] += 1
    three_words_counter[triple] += 1

def collect_statistics(path, output_file):
    two_words_counter = Counter([])
    three_words_counter = Counter([])
    for file_name in os.listdir(path):
        update_counters(convert_to_list_of_lexems(path + file_name), 
                        two_words_counter, three_words_counter)
    next_word = {}
    for triple, frequency in three_words_counter.iteritems():
        if (triple[0], triple[1]) not in next_word:
            next_word[(triple[0], triple[1])] = []
        next_word[(triple[0], triple[1])].append((triple[2], float(frequency) / 
                two_words_counter[(triple[0], triple[1])]))
    with open(output_file, 'w') as f:
        json.dump([(words[0], words[1], list_of_candidates) 
                   for words, list_of_candidates in next_word.iteritems()], f) 
        
def generate_sentence(next_word_candidates):
    first_word = UNIQUE_WORD
    second_word = UNIQUE_WORD
    sentence = ''
    end_of_sentence = False
    first_sentence_word = None
    while (not end_of_sentence):
        first_word, second_word = second_word, \
                generate_next_word(next_word_candidates[first_word, second_word])
        if (first_word == UNIQUE_WORD):
            first_sentence_word = second_word
        if (second_word in ENDS_OF_SENTENCES and 
                first_sentence_word.lower() in QUESTION_WORDS):
            sentence += '?'
        elif (second_word in PUNCTUATION or 
                first_word == UNIQUE_WORD or second_word[0] == "\'"):
            sentence += second_word
        elif (second_word == UNIQUE_WORD):
            end_of_sentence = True
        else:
            sentence += ' ' + second_word
    return sentence

def generate_next_word(candidates):
    probabilities = np.array([item[1] 
                            for index, item in enumerate(candidates)])
    index_choice = np.random.choice(len(candidates), 1, p = probabilities)[0]
    return candidates[index_choice][0]   

def generate_text(next_word_candidates, min_number_of_sentences):
    current_number_of_sentences = 0
    text = []
    while (current_number_of_sentences < min_number_of_sentences):
        number_of_paragraph_sentences = max(int(10 + 10 * np.random.randn() + 0.5), 1);
        current_number_of_sentences += number_of_paragraph_sentences;
        paragraph = []
        for i in range(number_of_paragraph_sentences):
            paragraph.append(generate_sentence(next_word_candidates))
        text.append(" ".join(paragraph));
    return "\n\n".join(text)

collect_statistics('corpus/', 'statistics.json')
with open('statistics.json', 'r') as f:
    statistics = json.load(f)
next_words = {}
for index, value in enumerate(statistics):
    next_words[(value[0], value[1])] = value[2]
    
text = generate_text(next_words, 3000)
f = open("text.txt", "w")
f.write(text)
f.close()