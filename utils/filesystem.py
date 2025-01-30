import os
from typing import Optional
from xmlrpc.client import Boolean
from fastapi import HTTPException

import logging
from utils.s3 import s3_client

from constants import (
    s3_bucket_name,
    s3_bucket_path,
    cloud_mode_enabled,
    local_assets_path,
    system_encoding,
)

assets_path = s3_bucket_path if cloud_mode_enabled else local_assets_path


def check_local_file_exists(file_path: str) -> bool:

    joined_path = os.path.join(assets_path, file_path)
    normalized_file_path = os.path.normpath(joined_path)
    path_exists = os.path.exists(normalized_file_path)

    return path_exists


def check_bucket_file_exists(file_path: str) -> bool:

    joined_path = f"{assets_path}/{file_path}"

    try:
        if not s3_client:
            return False

        object_head = s3_client.head_object(Bucket=s3_bucket_name, Key=joined_path)

        print("object_head", object_head)

        return True
    except Exception as e:
        print(e)
        return False


def check_file_exists(file_path: str) -> bool:
    exists = (
        check_bucket_file_exists(file_path)
        if cloud_mode_enabled
        else check_local_file_exists(file_path)
    )

    return exists


def check_local_directory_exists(directory_path: str) -> bool:

    joined_path = os.path.join(assets_path, directory_path)
    normalized_directory_path = os.path.normpath(joined_path)
    path_exists = os.path.exists(normalized_directory_path)

    is_directory = os.path.isdir(normalized_directory_path) if path_exists else False

    return is_directory


def check_bucket_directory_exists(directory_path: str) -> bool:

    joined_path = f"{assets_path}/{directory_path}"

    try:
        if not s3_client:
            return False

        s3_objects = s3_client.list_objects_v2(
            Bucket=s3_bucket_name, Prefix=joined_path
        )

        return bool(s3_objects.get("Contents"))
    except Exception as e:
        print(e)
        return False


def check_directory_exists(directory_path: str) -> bool:
    exists = (
        check_bucket_directory_exists(directory_path)
        if cloud_mode_enabled
        else check_local_directory_exists(directory_path)
    )

    return exists


def open_text_file(file_path: str) -> Optional[str]:

    if cloud_mode_enabled:
        if not s3_client:
            error_message = "S3 client not initialized, cannot open file"
            logging.error(error_message)
            raise HTTPException(status_code=500, detail=error_message)

        joined_path = f"{assets_path}/{file_path}"

        try:
            s3_object = s3_client.get_object(Bucket=s3_bucket_name, Key=joined_path)

            s3_file_content = s3_object["Body"].read().decode("utf-8")

            return s3_file_content
        except Exception:
            # print(e)
            return None
    else:
        joined_path = os.path.join(assets_path, file_path)
        normalized_file_path = os.path.normpath(joined_path)

        if not os.path.exists(normalized_file_path):
            return None

        with open(normalized_file_path, "r", encoding=system_encoding) as file:
            file_content = file.read()

            return file_content


def save_file(file_path: str, content: bytes) -> Boolean:
    if cloud_mode_enabled:
        if not s3_client:
            error_message = "S3 client not initialized, cannot open file"
            logging.error(error_message)
            raise HTTPException(status_code=500, detail=error_message)

        joined_path = f"{assets_path}/{file_path}"

        try:
            s3_client.put_object(Bucket=s3_bucket_name, Key=joined_path, Body=content)

            return True
        except Exception as e:
            print(e)
            return False

    return False


def delete_file(file_path: str) -> Boolean:
    if cloud_mode_enabled:
        if not s3_client:
            error_message = "S3 client not initialized, cannot open file"
            logging.error(error_message)
            raise HTTPException(status_code=500, detail=error_message)

        joined_path = f"{assets_path}/{file_path}"

        try:
            s3_client.delete_object(
                Bucket=s3_bucket_name,
                Key=joined_path,
            )

            return True
        except Exception as e:
            print(e)
            return False

    return False


def list_local_directory(directory_path: Optional[str], type: str) -> list:

    joined_path = (
        os.path.join(assets_path, directory_path) if directory_path else assets_path
    )
    normalized_directory_path = os.path.normpath(joined_path)

    is_directory = os.path.isdir(normalized_directory_path)

    files = (
        [
            d
            for d in os.listdir(normalized_directory_path)
            if (
                os.path.isdir(os.path.join(normalized_directory_path, d))
                and (type == "directory" or type == "all")
            )
            or (
                os.path.isfile(os.path.join(normalized_directory_path, d))
                and (type == "file" or type == "all")
            )
        ]
        if is_directory
        else []
    )

    return files


def list_bucket_directory(directory_path: Optional[str], type: str) -> list:
    if not s3_client:
        error_message = "S3 client not initialized, cannot list directory"
        logging.error(error_message)
        raise HTTPException(status_code=500, detail=error_message)

    joined_path = f"{assets_path}/{directory_path}" if directory_path else assets_path

    try:
        s3_objects = s3_client.list_objects_v2(
            Bucket=s3_bucket_name, Prefix=joined_path
        )

        if not s3_objects.get("Contents"):
            return []

        keys = [content["Key"] for content in s3_objects.get("Contents")]
        path_children = set()

        for key in keys:
            clean_key = key.replace(f"{joined_path}/", "")

            if "/" in clean_key and (type == "directory" or type == "all"):
                path_children.add(clean_key.split("/")[0])
            elif "/" not in clean_key and type == "file" or type == "all":
                path_children.add(clean_key)

        result = [child for child in path_children]

        return result
    except Exception as e:
        print(e)
        return []


def list_directory(directory_path: Optional[str], type: str) -> list:
    files = (
        list_bucket_directory(directory_path, type)
        if cloud_mode_enabled
        else list_local_directory(directory_path, type)
    )

    return files
