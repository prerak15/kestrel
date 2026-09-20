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


def build_row(elem, table_name):

    if table_name == "posts":
        return {
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
    elif table_name == "postlinks":
        return {
            "id": to_int(elem.attrib.get("Id")),
            "creation_date": to_datetime(elem.attrib.get("CreationDate")),
            "post_id": to_int(elem.attrib.get("PostId")),
            "related_post_id": to_int(elem.attrib.get("RelatedPostId")),
            "link_type_id": to_int(elem.attrib.get("LinkTypeId")),
        }
    else:
        raise ValueError(f"unknown table: {table_name}")


def load_db(table_name, COLUMNS, xml_path, batch_size=1000):

    load_dotenv("deploy/.env")
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise SystemExit("POSTGRES_PASSWORD not set - check deploy/.env")

    placeholders = ", ".join(f"%({c})s" for c in COLUMNS)

    INSERT_SQL = f"INSERT INTO {table_name} ({', '.join(COLUMNS)}) VALUES ({placeholders})"

    batch = []

    with (
        psycopg.connect(
            host="localhost", dbname="kestrel", user="prerak", password=password
        ) as conn,
        conn.cursor() as cur,
    ):
        context = ET.iterparse(xml_path, events=("start", "end"))
        _, root = next(context)
        count = 0
        for event, elem in context:
            if event == "end" and elem.tag == "row":
                count += 1
                item_data = build_row(elem, table_name)
                batch.append(item_data)
                if count % 100_000 == 0:
                    print(f"rows parsed {count}", flush=True)

                if len(batch) >= batch_size:
                    cur.executemany(INSERT_SQL, batch)
                    batch = []

                elem.clear()
                root.clear()

        if batch:
            cur.executemany(INSERT_SQL, batch)
    print(f"done: {count:,} rows loaded", flush=True)


def load_posts(folder):
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

    load_db("posts", COLUMNS, os.path.join(folder, "Posts.xml"))


def load_postlinks(folder):
    COLUMNS = ["id", "creation_date", "post_id", "related_post_id", "link_type_id"]

    load_db("postlinks", COLUMNS, os.path.join(folder, "PostLinks.xml"))


folder = sys.argv[1]

load_posts(folder)
load_postlinks(folder)
