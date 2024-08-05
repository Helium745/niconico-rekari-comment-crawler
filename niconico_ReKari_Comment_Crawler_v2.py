import requests
import logging
import time
import sys
import os
from datetime import datetime
from tqdm import tqdm
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)
format = "%(asctime)s | %(name)s[%(levelname)s]: %(message)s"
logging.basicConfig(level=logging.INFO, format=format)

session = requests.Session()

failed_counts = 0

class MyException(Exception): ...

class MakeXML():
    def __init__(self, vid_id, folder) -> None:
        self.id_list = []
        self.vid_id = vid_id
        self.filename = os.path.join(folder, f"{vid_id}.xml")
        self.folder = folder
        self.failed_counts = 0
        self.json_url = f"https://nvapi.nicovideo.jp/v1/tmp/comments/{vid_id}?_frontendId=6&_frontendVersion=0.0.0"
        if os.path.isfile(self.filename):
            self.__read_xml()
        else:
            self.packet = ET.Element("packet")
    
    def get_comments(self) -> int:
        logger.info(self.vid_id + "のコメントを取得中…")
        try:
            response = session.get(self.json_url)
        except:
            logger.warning(self.vid_id + "のコメントを取得できませんでした。")
            return
        if 'json' in response.headers.get('content-type'):
            data = response.json()
        else:
            logger.warning("帰ってきたデータがjsonじゃないらしい")
            return
        global failed_counts
        if data["meta"]["status"] == 200:
            if failed_counts >= 1: failed_counts = 0
            self.__add_comments(data["data"]["comments"])
        else:
            logger.warning("取得に失敗しました。ErrorCode:" + str(data["meta"]["status"]))
            failed_counts += 1
            self.failed_counts += 1
            if self.failed_counts >= 3:
                logger.warning(f"{self.vid_id}が見れなくなっているかもしれません。")
    
    def __add_comments(self, data) -> None:
        index = 0
        chat_list = []
        for content in reversed(data):
            if content["id"] in self.id_list:
                continue
            chat_list.append(ET.SubElement(self.packet, "chat"))
            chat_list[index].set("user_id", content["id"])
            chat_list[index].set("date", str(int(datetime.fromisoformat(content["postedAt"]).timestamp())))
            chat_list[index].set("vpos", str(round(content["vposMsec"] / 10)))
            chat_list[index].set("mail", content["command"])
            chat_list[index].text = content["message"]
            self.id_list.append(content["id"])
            index += 1
        logger.info(self.vid_id + ": " + str(index) + "コメントを取得しました。")
        logger.info(self.vid_id + ": 総コメント数: " + str(len(self.id_list)))
    
    def write_xml(self) -> None:
        logger.info(self.filename + "に保存しています…")
        tree = ET.ElementTree(self.packet)
        ET.indent(tree, space='  ')
        tree.write(self.filename, encoding='utf-8', xml_declaration=True)
        logger.info("保存しました。")

    def __read_xml(self) -> None:
        logger.info(self.vid_id + ": XMLファイルの読込中です…")
        tree = ET.parse(self.filename)
        self.packet = tree.getroot()
        for e in self.packet.findall("chat"):
            self.id_list.append(e.get("user_id"))
        logger.info(self.vid_id + ": 読み込み完了。")


def main():
    print("ニコニコ動画(Re:仮)用コメント取るやつ Ver.2")
    print()

    with open("videos_list.txt", encoding="UTF-8") as file:
        videos_list = file.read().splitlines()
    
    args = sys.argv

    if len(args) >= 2:
        wait_second = int(args[1])
    else:
        while True:
            try:
                wait_second = int(input("待機秒数を入力してください。(ex. 5): "))
            except ValueError:
                continue
            break

    folder_name = os.path.join("xml", "parser_v2")
    os.makedirs(folder_name, exist_ok=True)

    logger.info("コメントのクロールを開始します。")

    instances = []
    for video_id in videos_list:
        instances.append(MakeXML(video_id, folder_name))

    try:
        while True:
            for i in range(len(videos_list)):
                instances[i].get_comments()
                if failed_counts >= 8:
                    raise MyException()
                for _ in tqdm(range(wait_second), desc="待機中…", ascii=" >-"):
                    time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Ctrl+C -> コメントのクロールを中断しました。")
    except MyException:
        logger.error("取得に失敗した回数が8回に達したため中断しました。")
    except Exception as e:
        logger.error(e)

    for i in range(len(videos_list)):
        instances[i].write_xml()

if __name__ == "__main__":
    main()

