#data crawl
#package and function for spider
(
  cd fission

  fission package create --spec --name mharvesters \
    --source ./harvester/__init__.py \
    --source ./harvester/base.py \
    --source ./harvester/refresh.py \
    --source ./harvester/requirements.txt \
    --source ./harvester/build.sh \
    --env python \
    --buildcmd './build.sh'

  fission fn create --name refresh \
    --spec\
    --pkg mharvesters \
    --env python \
    --entrypoint "refresh.main"\
    --ft=1600

  fission fn create --name base \
    --spec\
    --pkg mharvesters \
    --env python \
    --entrypoint "base.main"\
    --ft=43200
)
# activate
fission spec apply --specdir ./specs --wait

#package and function for enqueue 
(
  cd fission
fission package create --spec --name mqueue \
  --source ./mqueue/__init__.py \
  --source ./mqueue/mqueue.py \
  --source ./mqueue/requirements.txt \
  --source ./mqueue/build.sh \
  --env python \
  --buildcmd './build.sh'

fission function create --spec --name mqueue \
  --pkg mqueue \
  --env python \
  --entrypoint "mqueue.main"
)

# httptrigger and mqtrigger
(

fission timer create --spec --name mtimer --function refresh --cron "@every 2h"
fission httptrigger create --spec --name mqueue --url "/mqueue/{topic}" --method POST --function mqueue

fission function create --name mprocessor --spec --env nodejs --code ./mprocessor.js --fntimeout=120

fission mqtrigger create --name mprocessing \
  --spec\
  --function mprocessor \
  --mqtype redis\
  --mqtkind keda\
  --topic mdata \
  --resptopic moutputdata \
  --errortopic errors \
  --maxretries 3 \
  --metadata address=redis-headless.redis.svc.cluster.local:6379\
  --metadata listLength=100\
  --metadata listName=mdata
)



# package function and mqtrigger for addmoutputdata. So it can auto add data to ES from redis.
(
  fission package create --spec --name addmoutputdata \
    --source ./addmoutputdata/__init__.py \
    --source ./addmoutputdata/addmoutputdata.py \
    --source ./addmoutputdata/requirements.txt \
    --source ./addmoutputdata/build.sh \
    --env python \
    --buildcmd './build.sh'


  fission fn create --name addmoutputdata \
    --spec\
    --pkg addmoutputdata \
    --env python \
    --entrypoint "addmoutputdata.main"\
    --ft=1600


  fission mqtrigger create --name add-moutputdata\
    --spec\
    --function addmoutputdata \
    --mqtype redis \
    --mqtkind keda \
    --topic moutputdata \
    --errortopic errors \
    --maxretries 3 \
    --metadata address=redis-headless.redis.svc.cluster.local:6379\
    --metadata listLength=100\
    --metadata listName=moutputdata
)

fission spec apply --specdir ./specs --wait

# cmd for creating index moutputdata
curl -XPUT -k 'https://127.0.0.1:9200/moutputdata' \
   --user 'elastic:elastic' \
   --header 'Content-Type: application/json' \
   --data '{
  "settings": {
    "index": {
      "number_of_shards": 3,
      "number_of_replicas": 1
    },
    "analysis": {
      "analyzer": {
        "hashtag_analyzer": {
          "type": "custom",
          "tokenizer": "keyword",
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "metadata": {
        "type": "object",
        "properties": {
          "post_id": {
            "type": "keyword"
          },
          "created_time": {
            "type": "date",
            "format": "strict_date_optional_time||epoch_millis"
          },
          "url": {
            "type": "keyword"
          },
          "language": {
            "type": "keyword"
          },
          "region": {
            "type": "keyword"
          },
          "processed_at": {
            "type": "date",
            "format": "strict_date_optional_time||epoch_millis"
          }
        }
      },
      "author": {
        "type": "object",
        "properties": {
          "acct": {
            "type": "keyword"
          },
          "display_name": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword",
                "ignore_above": 256
              }
            }
          },
          "profile_url": {
            "type": "keyword"
          },
          "domain": {
            "type": "keyword"
          },
          "join_date": {
            "type": "date",
            "format": "strict_date_optional_time||epoch_millis"
          }
        }
      },
      "content": {
        "type": "object",
        "properties": {
          "text": {
            "type": "text",
            "analyzer": "english"
          },
          "hashtags": {
            "type": "text",
            "analyzer": "hashtag_analyzer",
            "fields": {
              "keyword": {
                "type": "keyword"
              }
            }
          },
          "mentions": {
            "type": "keyword"
          },
          "word_count": {
            "type": "integer"
          }
        }
      },
      "engagement": {
        "type": "object",
        "properties": {
          "favorites": {
            "type": "nested",
            "properties": {
              "acct": {
                "type": "keyword"
              },
              "display_name": {
                "type": "text"
              },
              "created_time": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
              },
              "url": {
                "type": "keyword"
              },
              "Domain": {
                "type": "keyword"
              },
              "note": {
                "type": "text"
              },
              "region": {
                "type": "keyword"
              }
            }
          },
          "reblogs": {
            "type": "nested",
            "properties": {
              "acct": {
                "type": "keyword"
              },
              "display_name": {
                "type": "text"
              },
              "created_time": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
              },
              "url": {
                "type": "keyword"
              },
              "Domain": {
                "type": "keyword"
              },
              "note": {
                "type": "text"
              },
              "region": {
                "type": "keyword"
              }
            }
          },
          "replies": {
            "type": "nested",
            "properties": {
              "acct": {
                "type": "keyword"
              },
              "display_name": {
                "type": "text"
              },
              "created_time": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
              },
              "url": {
                "type": "keyword"
              },
              "Domain": {
                "type": "keyword"
              },
              "note": {
                "type": "text"
              },
              "region": {
                "type": "keyword"
              },
              "content": {
                "type": "text"
              }
            }
          }
        }
      }
    }
  }
}' | jq '.'



