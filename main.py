from __future__ import unicode_literals

from functools import lru_cache

from fastapi import FastAPI, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from haystack.document_stores.pinecone import PineconeDocumentStore
from haystack.nodes import FARMReader, DensePassageRetriever
from haystack.pipelines import ExtractiveQAPipeline
from pytube import YouTube

import config
from helpers import generate_docs, timed_lru_cache

app = FastAPI()


@lru_cache()
def get_settings():
    return config.Settings()


@timed_lru_cache(600)
def setup_qa(yt_vid_id: str):
    document_store = PineconeDocumentStore(
        api_key=get_settings().pinecone_key,
        environment='us-west1-gcp',
        index=yt_vid_id
    )
    retriever = DensePassageRetriever(
        document_store=document_store,
        query_embedding_model="facebook/dpr-question_encoder-single-nq-base",
        passage_embedding_model="facebook/dpr-ctx_encoder-single-nq-base",
        max_seq_len_query=64,
        max_seq_len_passage=256,
        batch_size=2,
        use_gpu=True,
        embed_title=True,
        use_fast_tokenizers=True
    )
    reader = FARMReader(model_name_or_path='deepset/bert-base-cased-squad2')

    qa_dict = {"store": document_store, "retriever": retriever, "reader": reader}

    return qa_dict


@timed_lru_cache(600)
def create_pipeline(reader, retriever):
    return ExtractiveQAPipeline(reader=reader, retriever=retriever)


@app.get("/youtube/{yt_vid_id}")
async def read_item(yt_vid_id: str, settings: config.Settings = Depends(get_settings), qa_setup=Depends(setup_qa)):
    yt = YouTube(f"https://youtu.be/{yt_vid_id}")
    caption = yt.captions.get_by_language_code('a.en')
    srt_captions = caption.generate_srt_captions()
    docs = generate_docs(srt_string=srt_captions, vid_title=yt.title)
    qa_setup['store'].write_documents(docs)
    qa_setup['store'].update_embeddings(
        retriever=qa_setup['retriever'],
        batch_size=16
    )

    return {"message": "Store updated"}


@app.get("/youtube/question/{yt_vid_id}/{question}")
async def answer_questions(yt_vid_id: str, question: str, qa_setup=Depends(setup_qa)):
    pipeline = create_pipeline(retriever=qa_setup['retriever'], reader=qa_setup['reader'])
    answer = pipeline.run(question)
    json_answer = jsonable_encoder(answer)

    return JSONResponse(content=json_answer)
