import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

import psycopg
from dotenv import load_dotenv


def to_int(value):
    if value is None:
        return None
    return int(value)


def to_datetime(value):
    if value is None:
        return None
    return datetime.fromisoformat(value)


def to_tags(value):
    if value is None:
        return None
    return [t for t in value.split("|") if t]


def load_posts(batch_size=1000):

    load_dotenv("deploy/.env")
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise SystemExit("POSTGRES_PASSWORD not set - check deploy/.env")

    COLUMNS = [
        "id",
        "post_type_id",
        "creation_date",
        "score",
        "body",
        "comment_count",
        "content_license",
        "accepted_answer_id",
        "view_count",
        "title",
        "tags",
        "answer_count",
        "parent_id",
        "owner_user_id",
        "owner_display_name",
        "closed_date",
        "favorite_count",
    ]

    placeholders = ", ".join(f"%({c})s" for c in COLUMNS)

    INSERT_SQL = f"INSERT INTO posts ({', '.join(COLUMNS)}) VALUES ({placeholders})"

    batch = []

    with (
        psycopg.connect(
            host="localhost", dbname="kestrel", user="prerak", password=password
        ) as conn,
        conn.cursor() as cur,
    ):
        context = ET.iterparse(sys.argv[1], events=("start", "end"))
        _, root = next(context)
        for event, elem in context:
            if event == "end" and elem.tag == "row":
                item_data = {
                    "id": to_int(elem.attrib.get("Id")),
                    "post_type_id": to_int(elem.attrib.get("PostTypeId")),
                    "creation_date": to_datetime(elem.attrib.get("CreationDate")),
                    "score": to_int(elem.attrib.get("Score")),
                    "body": elem.attrib.get("Body"),
                    "comment_count": to_int(elem.attrib.get("CommentCount")),
                    "content_license": elem.attrib.get("ContentLicense"),
                    "accepted_answer_id": to_int(elem.attrib.get("AcceptedAnswerId")),
                    "view_count": to_int(elem.attrib.get("ViewCount")),
                    "title": elem.attrib.get("Title"),
                    "tags": to_tags(elem.attrib.get("Tags")),
                    "answer_count": to_int(elem.attrib.get("AnswerCount")),
                    "parent_id": to_int(elem.attrib.get("ParentId")),
                    "owner_user_id": to_int(elem.attrib.get("OwnerUserId")),
                    "owner_display_name": elem.attrib.get("OwnerDisplayName"),
                    "closed_date": to_datetime(elem.attrib.get("ClosedDate")),
                    "favorite_count": to_int(elem.attrib.get("FavoriteCount")),
                }
                batch.append(item_data)

                if len(batch) >= batch_size:
                    cur.executemany(INSERT_SQL, batch)
                    batch = []

                elem.clear()
                root.clear()

        if batch:
            cur.executemany(INSERT_SQL, batch)


load_posts()
