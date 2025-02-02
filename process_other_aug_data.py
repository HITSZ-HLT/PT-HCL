#!/usr/bin/env python3
# -*- coding:UTF8 -*-
# ------------------
# @File Name: process_other_aug_data.py
# @Version: 
# @Author: ZixiaoChen
# @Mail: 20s151161@stu.hit.edu.cn
# @For: 
# @Created Time: Tues 22 June 2021 14:58:00
# ------------------
import numpy as np
import string
import nltk
import math
import random
import time
from nltk.corpus import wordnet as wn
from itertools import chain
import spacy

nlp = spacy.load('en_core_web_sm')

import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')

import gensim
from sklearn.datasets import fetch_20newsgroups
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
from gensim.corpora import Dictionary
import os
from pprint import pprint

replace_dic = {'dt': ['fm','la','hc','a','cc'],
               'hc': ['fm','la','dt','a','cc'],
               'fm': ['hc','la','dt','a','cc'],
               'la': ['fm','hc','dt','a','cc'],
               'a': ['fm','la','dt','hc','cc'],
               'cc': ['fm','la','dt','hc','a'],
               'aet_hum': ['antm_ci', 'ci_esrx', 'cvs_aet'],
               'antm_ci': ['aet_hum', 'ci_esrx', 'cvs_aet'],
               'ci_esrx': ['aet_hum', 'antm_ci', 'cvs_aet'],
               'cvs_aet': ['aet_hum', 'antm_ci', 'ci_esrx'],
}

mask_dir = './augment_data/mask/'
replace_dir = './augment_data/replace/'
sentence_dir = './augment_data/sentence/'

def load_seed_words(dataname, percent=1):
    path = './seed_words/'+dataname+'.seed'
    print(path)
    seed_words = {}
    fin = open(path)
    for line in fin:
        line = line.strip()
        if not line:
            continue
        word, weight = line.split()
        if float(weight) <= 0:
            continue
        seed_words[word] = float(weight)
    fin.close()
    save_len = int(len(seed_words) * percent)
    seed_words = sorted(seed_words.items(), key=lambda a: -a[1])
    word_dic = {}
    for word, weight in seed_words:
        word_dic[word] = weight
        save_len -= 1
    return word_dic

def tokenize(text):
    """
    将text分词，并去掉停用词。STOPWORDS -是指Stone, Denis, Kwantes(2010)的stopwords集合.
    :param text:需要处理的文本
    :return:去掉停用词后的"词"序列
    """
    return [token for token in simple_preprocess(text) if token not in STOPWORDS]

def process(method,filename):#method:random_word,spelling,delete,dp
    fin = open(filename, 'r', encoding='utf-8', errors='ignore')
    fout_mask = open(mask_dir+filename.split('/')[-1], 'w', encoding='utf-8')
    fout_replace = open(replace_dir+filename.split('/')[-1], 'w', encoding='utf-8')
    fout_sentence = open(sentence_dir+method+'_'+filename.split('/')[-1], 'w', encoding='utf-8')
    dataname = filename.split('/')[-1].split('.raw')[0].strip().lower()
    lines = fin.readlines()
    fin.close()

    fin2 = open(filename, 'r', encoding='utf-8', errors='ignore')
    lines2 = fin2.readlines()
    fin2.close()
    replace_dict={}
    documents=[]
    for i in range(0, len(lines2), 3):
        documents.append(lines2[i])
        if 'dp' in method:
            text=lines[i].lower().strip()
            text2=' '.join(nltk.word_tokenize(text)).lower()
            doc=nlp(text2)
            for token in doc:
                if token.tag_ not in replace_dict:
                    replace_dict[token.tag_]=[token.text]
                else:
                    replace_dict[token.tag_].append(token.text)
    processed_docs = [tokenize(doc) for doc in documents]
    word_count_dict = Dictionary(processed_docs)
    word_count_dict.filter_extremes(no_below=20,no_above=0.1)
    bag_of_words_corpus = [word_count_dict.doc2bow(pdoc) for pdoc in processed_docs]
    model_name =filename+".lda"#"./ldamodel/" +
    
    lda_model = gensim.models.LdaModel(bag_of_words_corpus, num_topics=30, id2word=word_count_dict, passes=15)#50 20 #1的效果其实也还行
    lda_model.save(model_name)
    top_topics = lda_model.top_topics(bag_of_words_corpus)
    lda_words=[]
    topk=15
    f_look=open(filename+"_topic_words_top20", 'w', encoding='utf-8', errors='ignore')
    for x in top_topics:
        for i in range(topk):
            if i <len(x[0]):
               
                lda_words.append(x[0][i][1])
        tmp=[]
        for y in x[0][:]:
            tmp.append(y[1])
        print(tmp)
        f_look.write(str(tmp)+'\n')
    for i in range(0, len(lines), 3):
        text = lines[i].lower().strip()
        target = lines[i+1].lower().strip()
        stance = lines[i+2].lower().strip() 
        # deriving masked data
        mask_string = text + '\n' + '[MASK]' + '\n' + stance + '\n'
        # deriving replaced data
        random_id = random.randint(0,len(replace_dic[dataname])-1)
        replace_target = replace_dic[dataname][random_id]
        replace_string = text + '\n' + replace_target + '\n' + stance + '\n'
        # deriving masked sentence's data
        text_list = text.split()
        sentence = []
        if method=='dp':
            text2=' '.join(nltk.word_tokenize(text)).lower()
            doc=nlp(text2)
            for token in doc:
                if token.text in word_dic:
                   sentence.append('['+token.tag_+']')
                else:
                    sentence.append(token.text)
        elif method=='dp_stance':
            text2=' '.join(nltk.word_tokenize(text)).lower()
            doc=nlp(text2)
            for token in doc:
                if token.text in word_dic:
                   sentence.append('['+stance+'_'+token.tag_+']')
                else:
                    sentence.append(token.text)
        elif method=='dp_replace':
            text2=' '.join(nltk.word_tokenize(text)).lower()
            doc=nlp(text2)
            for token in doc:
                if token.text in word_dic:
                    tlist=replace_dict[token.tag_]
                    replaceword=tlist[random.randint(0,len(tlist)-1)]
                    sentence.append(replaceword)
                else:
                    sentence.append(token.text)
        elif method=='lda':
            for token in text_list:
                if token in lda_words:
                    sentence.append('[LDA_MASK]')
                else:
                    sentence.append(token)
        else:
            for token in text_list:
                if token in word_dic:
                    if method=='mask':
                        sentence.append('[MASK]')
                    if method=='random_word':
                        n_text_list=text_list[:]
                        for token in text_list:
                            if token in word_dic:
                                n_text_list.remove(token)
                        random_word=n_text_list[random.randint(0,len(n_text_list)-1)]
                        sentence.append(random_word)
                    if method=='spelling':
                        randlist=np.random.rand(len(token))
                        count=0
                        random_rate=0.4
                        spelling_word=''
                        for ch in token:
                            if random_rate>randlist[count]:
                                s = string.ascii_letters
                                spelling_word+=random.choice(s).lower()
                            else:
                                spelling_word+=ch
                            count+=1
                        sentence.append(spelling_word)
                    if method=='delete':
                        continue
                else:
                    sentence.append(token)
        sentence_string = ' '.join(sentence) + '\n' + target + '\n' + stance + '\n'
        # saving data
        fout_mask.write(mask_string)
        fout_replace.write(replace_string)
        fout_sentence.write(sentence_string)
    fout_mask.close()
    fout_replace.close()
    fout_sentence.close()

    

if __name__=="__main__":
    
    for method in ['lda']:
        '''
        process( method,'./raw_data/cvs_aet.raw')
        process( method,'./raw_data/ci_esrx.raw')
        process( method,'./raw_data/antm_ci.raw')
        process( method,'./raw_data/aet_hum.raw')
        '''
        process( method,'./raw_data/fm.raw')
        process( method,'./raw_data/la.raw')
        process( method,'./raw_data/hc.raw')
        process( method,'./raw_data/dt.raw')
        process( method,'./raw_data/a.raw')
        process( method,'./raw_data/cc.raw')
        
    

