import logging
from datetime import timedelta, datetime
from functools import lru_cache, wraps


import pysrt


def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expiration = datetime.utcnow() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.utcnow() >= func.expiration:
                func.cache_clear()
                func.expiration = datetime.utcnow() + func.lifetime

            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache


def generate_docs(srt_string: str, vid_title: str):
    subs = pysrt.from_string(srt_string)
    contexts = []
    meta_data = []
    for i in range(1, subs[-1].start.minutes):
        sub_file = subs.slice(starts_after={'minutes': i - 1}, ends_before={'minutes': i})
        contexts.append(sub_file.text.replace('\n', " "))
        context_meta_data = {}
        for x in range(0, len(sub_file)):
            context_meta_data[f"line{x}_text"] = sub_file[x].text_without_tags
            context_meta_data[f"line{x}_start_time"] = sub_file[x].start.ordinal
            context_meta_data[f"line{x}_end_time"] = sub_file[x].end.ordinal
            # current_meta_data = {'text': sub_file[x].text_without_tags, "start_time": sub_file[x].start.ordinal,
            #                      'end_time': sub_file[x].end.ordinal}
            # context_meta_data.append(current_meta_data)
        meta_data.append(context_meta_data)
    docs = [{
        "content": context,
        "meta": context_meta

    } for context, context_meta in zip(contexts, meta_data)]
    return docs


