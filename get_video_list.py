import requests
import logging
import time
import json
import os
from datetime import datetime
from tqdm import tqdm

def main():
    print("ニコニコ動画(Re:仮)用動画一覧取るやつ Ver.1")
    print()
    json_url = "https://nvapi.nicovideo.jp/v1/tmp/videos?count=10&_frontendId=6&_frontendVersion=0.0.0"
    headers = {"content-type": "application/json"}
    logger = logging.getLogger(__name__)
    format = "%(asctime)s | %(name)s[%(levelname)s]: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=format)
    list = []
    id_list = []
    logger.info("動画一覧の取得を開始します。")
    try:
        while len(list) < 1000:
            response = requests.get(json_url, headers=headers)
            data = response.json()
            if data["meta"]["status"] != 200:
                logger.warning("動画情報が取得できませんでした。ErrorCode:" + str(data["meta"]["status"]))
                for _ in tqdm(range(int(5))): time.sleep(1)
                continue
            logger.info("10個取得しました。")
            for content in data["data"]["videos"]:
                if not content["id"] in id_list:
                    list.append([content["id"], content["title"]])
                    id_list.append(content["id"])
            logger.info("現在の総数:" + str(len(list)))
            for _ in tqdm(range(int(5))): time.sleep(1)
    except KeyboardInterrupt:
        pass
    sorted_list = sorted(sorted(list, key=lambda x: x[0][2:]), key=lambda x: len(x[0]))
    if os.path.isfile("git\\watchable_list.md"):
        os.rename("git\\watchable_list.md", "git\\watchable_list" + str(int(time.time())) + ".md")
    with open("git\\watchable_list.md", "w", encoding='utf-8') as file:
        file.write("# ニコニコ動画(Re:仮)で見れる動画の一覧\n")
        for content in sorted_list:
            file.write("- [" + content[1] + "](https://www.nicovideo.jp/watch_tmp/" + content[0] + ")\n")
    if os.path.isfile("videos_list.txt"):
        os.rename("videos_list.txt", "videos_list_" + str(int(time.time())) + ".txt")
    with open("videos_list.txt", "x", encoding='utf-8') as file:
        for content in sorted_list:
            file.write(content[0] + "\n")


if __name__ == "__main__":
    main()