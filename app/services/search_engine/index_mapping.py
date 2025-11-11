settings = {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "analysis": {
        "analyzer": {
            "folding_analyzer": {
                "tokenizer": "standard",
                "filter": ["lowercase", "asciifolding"],
            }
        }
    },
}


mappings = {
    "dynamic": "strict",
    "properties": {
        "DocumentID": {"type": "long"},
        "Price": {"type": "text"},
        "BoatLocation": {
            "type": "text",
            "analyzer": "folding_analyzer",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "BoatCityNameNoCaseAlnumOnly": {
            "type": "text",
            "analyzer": "folding_analyzer",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "NumberOfEngines": {"type": "long"},
        "MakeString": {
            "type": "text",
            "analyzer": "folding_analyzer",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "ModelYear": {"type": "long"},
        "Model": {"type": "text"},
        "BeamMeasure": {"type": "text"},
        "TotalEnginePowerQuantity": {"type": "text"},
        "NominalLength": {"type": "text"},
        "LengthOverall": {"type": "text"},
        "Engines": {"type": "text"},
        "GeneralBoatDescription": {"type": "text"},
        "AdditionalDetailDescription": {"type": "text"},
        "Link": {"type": "text", "index": False},
        "Images": {"type": "text", "index": False},
        "vector": {
            "type": "dense_vector",
            "dims": 3072,
            "index": True,
            "similarity": "l2_norm",
        },
    },
}
