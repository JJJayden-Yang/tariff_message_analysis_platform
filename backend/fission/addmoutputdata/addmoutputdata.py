import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Union
from flask import current_app, request
from elasticsearch8 import Elasticsearch

def convert_to_elasticsearch_date(date_str: Union[str, None]) -> Union[str, None]:
    """
    convert date
    1. "2023-02-16 00:00:00+00:00" → "2023-02-16T00:00:00Z"
    2. "2025-05-12 08:57:06.928000" → "2025-05-12T08:57:06.928Z"
    3. "2025-05-12T14:54:47.579Z" → keep
    """
    if not date_str or not isinstance(date_str, str):
        return None

    try:
        clean_str = date_str.strip()
        
    # solve time zone
        if "+00:00" in clean_str:
            dt_str = clean_str.replace("+00:00", "")
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            return f"{dt.isoformat(timespec='milliseconds')}Z"
        
        elif "." in clean_str and "T" not in clean_str:
            dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S.%f")
            return f"{dt.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds')}"
        
        elif "T" not in clean_str:
            dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
            return f"{dt.replace(tzinfo=timezone.utc).isoformat()}"

        return clean_str
    
    except Exception as e:
        current_app.logger.error(f"date transfer failed: {str(e)} | original date: {date_str}")
        return None

def ensure_index_mapping(es_client: Elasticsearch):

    mapping = {
        "mappings": {
            "properties": {
                "metadata.created_time": {
                    "type": "date",
                    "format": "strict_date_optional_time||yyyy-MM-dd HH:mm:ss.SSSSSS||yyyy-MM-dd HH:mm:ss||epoch_millis"
                },
                "author.join_date": {
                    "type": "date",
                    "format": "strict_date_optional_time||yyyy-MM-dd HH:mm:ss.SSSSSS||yyyy-MM-dd HH:mm:ss||epoch_millis"
                },
                "engagement.favorites.created_time": {
                    "type": "date",
                    "format": "strict_date_optional_time||epoch_millis"
                },
                "engagement.reblogs.created_time": {
                    "type": "date",
                    "format": "strict_date_optional_time||epoch_millis"
                },
                "engagement.replies.created_time": {
                    "type": "date",
                    "format": "strict_date_optional_time||yyyy-MM-dd HH:mm:ss.SSSSSS||epoch_millis"
                }
            }
        }
    }
    
    if not es_client.indices.exists(index="moutputdata"):
        es_client.indices.create(index="moutputdata", body=mapping)
    else:
        try:
            es_client.indices.put_mapping(index="moutputdata", body=mapping["mappings"])
        except Exception as e:
            current_app.logger.warning(f"mapping update fail: {str(e)}")

def process_post(post: Dict[str, Any]) -> Dict[str, Any]:

    # handle metadata
    if "metadata" in post:
        post["metadata"] = {
            **post["metadata"],
            "created_time": convert_to_elasticsearch_date(post["metadata"].get("created_time")) or "1970-01-01T00:00:00Z",
            "processed_at": convert_to_elasticsearch_date(post["metadata"].get("processed_at")) or datetime.now(timezone.utc).isoformat()
        }
    
    # handle author
    if "author" in post:
        post["author"] = {
            **post["author"],
            "join_date": convert_to_elasticsearch_date(post["author"].get("join_date")) or "1970-01-01T00:00:00Z"
        }
    
    # handle engagement
    if "engagement" in post:
        # 处理favorites
        for fav in post["engagement"].get("favorites", []):
            fav["created_time"] = convert_to_elasticsearch_date(fav.get("created_time")) or "1970-01-01T00:00:00Z"
        
        # reblogs
        for reblog in post["engagement"].get("reblogs", []):
            reblog["created_time"] = convert_to_elasticsearch_date(reblog.get("created_time")) or "1970-01-01T00:00:00Z"
        
        # reply
        for reply in post["engagement"].get("replies", []):
            reply["created_time"] = convert_to_elasticsearch_date(reply.get("created_time")) or "1970-01-01T00:00:00Z"
    
    return post

def main() -> str:
    es_client = Elasticsearch(
        'https://elasticsearch-master.elastic.svc.cluster.local:9200',
        verify_certs=False,
        ssl_show_warn=False,
        basic_auth=('elastic', 'elastic')
    )
    
    ensure_index_mapping(es_client)
    
    request_data = request.get_json(force=True)
    posts_to_process = [request_data] if isinstance(request_data, dict) else request_data

    success_count = 0
    failure_count = 0

    for post in posts_to_process:
        try:
        
            processed_post = process_post(post)
            doc_id = str(post["metadata"]["post_id"])

            es_client.index(
                index="moutputdata",
                id=doc_id,
                body=processed_post,
                refresh=True
            )
            success_count += 1
        except Exception as e:
            failure_count += 1
            post_id = post.get("metadata", {}).get("post_id", "unknown")
            current_app.logger.error(f"process fail {post_id}: {str(e)}", exc_info=True)

    current_app.logger.info(f"process finished - success: {success_count}, fail: {failure_count}")
    return 'ok' if failure_count == 0 else 'partial_ok'