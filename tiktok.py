# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from cqhttp import CQHttp
# 引入时间调度器 apscheduler 的 BlockingScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

# bot = CQHttp(api_root='http://127.0.0.1:5701/')


# 创建调度器实例
sched = BlockingScheduler()
interval_delay = 120

header = {
	"Host": "api.amemv.com",
	"Connection": "keep-alive",
	"Accept-Encoding": "gzip",
	"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"
}


def load_user_config():
	with open('config.json','rb') as f:
		config = json.load(f)
		return config


def get_latest_tiktok_id(config):
	nickname = config["name"]
	for i in init_data:
		if i["nickname"] == nickname:
			return i["latest_tiktok_id"]

def update_latest_tiktok_id(config, latest_tiktok_id):
	nickname = config["name"]
	for i in init_data:
		if i["nickname"] == nickname:
			i["latest_tiktok_id"] = latest_tiktok_id


def get_tiktok_list(sec_uid):
	video_url = 'https://www.iesdouyin.com/web/api/v2/aweme/post/?{0}'
	video_form = {
		"sec_uid": sec_uid,
		"count":"21",
		"max_cursor":"0",
		"aid":"1128",
		"_signature": '4hIiBAAAg525HWk-tq3rV-ISIh', # signature
		"dytk": ''# dytk
	}
	url = video_url.format(
        '&'.join([key + '=' + video_form[key] for key in video_form]))
	response = requests.get(url, headers=header).json()
	tiktok_list = response["aweme_list"]
	return tiktok_list


def monitor_worker(config):
	new_tiktok_list = []
	time_record = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
	print("开始查询：" + time_record)
	msg_queue = []
	# 获取用户数据
	tiktok_list = get_tiktok_list(config['sec_uid'])

	# 最后一次获取的抖音的id
	if len(tiktok_list) == 0:
		print(str(config["name"]) + "未获取到数据，请检查用户是否发过抖音")
	else:
		msg = str(config["name"]) + "：共有"+str(len(tiktok_list))+"条抖音"
		print(msg)
	msg = ""
	latest_tiktok_id = get_latest_tiktok_id(config)
	for i in tiktok_list:
		# aweme_id = 当前抖音的id
		aweme_id = i["aweme_id"]
		if int(aweme_id) > int(latest_tiktok_id):
			new_tiktok_list.append(i)
			update_latest_tiktok_id(config, aweme_id)

	if tiktok_list:
		print("发现" + str(len(new_tiktok_list)) + "条新抖音\n")
		for i in new_tiktok_list:
			share_desc = i["desc"]
			cover_img = "https://p9-dy.byteimg.com/img/" + i["video"]["cover"]["uri"] + "~c5_300x400.jpg"
			play_addr = "https://aweme.snssdk.com/aweme/v1/play/?video_id=" + i["video"]["play_addr"]["uri"] + "&line=0"
			msg = [{'type': 'at', 'data': {'qq': str(config['at'])}},
					{'type': 'text', 'data': {'text': '\n%s更新抖音啦！\n标题：%s\n封面：\n' % (config["name"],share_desc)}},
					{'type': 'image','data': {'file': cover_img}},
					{'type': 'text', 'data': {'text': '\n链接：%s\n' % play_addr}}]
			msg_queue.append(msg)

	else:
		print("未发现更新\n")
	return msg_queue


def tiktok_monitor():
	try:
		time_record = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
		print(time_record, 'Monitoring Tiktok ...')
		for config in configs:
			msg_queue = monitor_worker(config)
			if len(msg_queue) > 0:
				for msg in msg_queue:
					bot.send_group_msg_async(group_id=config['qq_group'], message=msg, auto_escape=False)
					time.sleep(0.1)
	except Exception as e:
		print("ERROR When monitoring %s" % e)
	finally:
		pass

try:
	sched.add_job(
	    tiktok_monitor, 'interval', seconds=interval_delay,
	    misfire_grace_time=interval_delay, coalesce=True, max_instances=15)
except Exception as e:
	print(e)
# 开始调度任务


def init_task():
	for config in configs:
		sec_uid = config["sec_uid"]
		latest_tiktok_id = get_tiktok_list(sec_uid)[0]["aweme_id"]
		d = {}
		d["nickname"] = config["name"]
		d["sec_uid"] = sec_uid
		d["latest_tiktok_id"] = latest_tiktok_id
		init_data.append(d)


if __name__ == '__main__':
	init_data = []
	configs = load_user_config()
	init_task()
	sched.start()
	print(init_data)




