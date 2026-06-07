from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

import uuid

from config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION
)

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=30
)


def ensure_collection():

    collections = client.get_collections().collections

    existing = {
        collection.name
        for collection in collections
    }

    if QDRANT_COLLECTION not in existing:

        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=512,
                distance=Distance.COSINE
            )
        )

        print(
            f"Created collection: {QDRANT_COLLECTION}"
        )

    else:

        print(
            f"Collection exists: {QDRANT_COLLECTION}"
        )


def upsert_student(
    student_id,
    embedding,
    payload
):

    point_id = str(
        uuid.uuid4()
    )

    point = PointStruct(
        id=point_id,
        vector=embedding.tolist(),
        payload=payload
    )

    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[point]
    )

    print(
        f"Student inserted: {student_id}"
    )

    print(
        f"Qdrant Point ID: {point_id}"
    )


def search_embedding(
    embedding,
    limit=1
):

    results = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=embedding.tolist(),
        limit=limit,
        with_payload=True
    )

    return results.points


def get_student_by_id(
    student_id
):

    results = client.scroll(
        collection_name=QDRANT_COLLECTION,
        scroll_filter={
            "must": [
                {
                    "key": "student_id",
                    "match": {
                        "value": student_id
                    }
                }
            ]
        },
        with_payload=True,
        limit=1
    )

    points = results[0]

    if len(points) == 0:
        return None

    return points[0]


def count_students():

    info = client.count(
        collection_name=QDRANT_COLLECTION,
        exact=True
    )

    return info.count
