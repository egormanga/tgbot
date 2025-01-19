#!/usr/bin/python3
# tgbot

import sys
if (not sys.flags.interactive): import warnings; warnings.filterwarnings('ignore', 'python-telegram-bot is using upstream urllib3. This is allowed but not supported by python-telegram-bot maintainers.')
import requests, telegram, telegram.ext
from telegram import *
from telegram.ext import *
from telegram.error import *
from utils import *; logstart('tgbot')

class TGBot(Slots):
	""" Meant to be `@singleton'-ed. """

	token: None
	base_url: None
	base_file_url: None
	webhook_port: None
	webhook_path: None
	webhook_url: None
	queue: ...
	updater: ...
	job_queue: ...
	dispatcher: ...
	persistence: None
	proxy_url: None
	proxy_list_url = "http://spys.me/proxy.txt"

	def __init__(self, token=None, *, webhook_port=None, webhook_path=None, webhook_url=None, log_filters=None, **kwargs):
		if (token is not None): self.token = token
		if (webhook_port is not None): self.webhook_port = webhook_port
		if (webhook_path is not None): self.webhook_path = webhook_path
		if (webhook_url is not None): self.webhook_url = webhook_url

		if (not self.token): raise ValueError(f"{self.__class__.__name__}.token is unspecified.")
		if (self.proxy_url is ...): self.proxy_url = self.get_proxy()
		self.updater = Updater(**parseargs(kwargs, token=self.token, base_url=self.base_url, base_file_url=self.base_file_url, persistence=self.persistence, request_kwargs={'proxy_url': self.proxy_url}, use_context=True))
		self.dispatcher = self.updater.dispatcher
		self.dispatcher.add_handler(LogHandler(log_filters))
		self.dispatcher.add_error_handler(self.error_callback)

	def run(self):
		if (not hasattr(self, 'queue')): self.start()
		self.idle()

	def start(self, **kwargs):
		if (self.webhook_port is not None):
			self.queue = self.updater.start_webhook(port=int(self.webhook_port), url_path=self.webhook_path, webhook_url=self.webhook_url, **kwargs)
		else:
			self.queue = self.updater.start_polling(**kwargs)
		self.job_queue = self.updater.job_queue

	def idle(self, **kwargs):
		self.updater.idle(**kwargs)

	def stop(self):
		self.updater.stop()

	@classmethod
	def get_proxy(cls, *, timeout=1):
		l = [None]+requests.get(cls.proxy_list_url).text.splitlines()
		for i in l:
			if (i is not None):
				if (not i or not i[0].isdigit()): continue
				if ('S' not in i): continue  # no ssl support
				i = i.split()[0]
			try: r = requests.get("https://api.telegram.org", proxies={'https': i}, timeout=timeout)
			except requests.RequestException as ex: continue
			else: return 'https://'+i if (i) else None
		else: raise WTFException('no proxy')

	def error_callback(self, update, context):
		logexception(context.error)

	def handler(self, handler, *args, **kwargs):
		@funcdecorator
		def decorator(f):
			def decorated(update, context):
				def reply(text=None, message_id=None, **kwargs):
					parseargs(kwargs, chat_id=update.effective_message.chat_id or (update.effective_chat or update.effective_user).id, text=text)
					msg = context.bot.edit_message_text(**parseargs(kwargs, message_id=message_id)) if (message_id is not None) else context.bot.send_message(**kwargs)
					context.user_data['_last_message_id'] = msg.message_id
					return msg
				update.reply = reply # TODO FIXME
				return f(update, context)
			self.dispatcher.add_handler(handler(*args, callback=decorated, **kwargs))
			return decorated
		return decorator

	@dispatch
	def command(self, f: function): return self.command(f.__name__)(f)
	@dispatch
	def command(self, cmd: str, **kwargs): return self.handler(CommandHandler, cmd[1:] if (cmd.startswith('/')) else cmd, **kwargs)

	@dispatch
	def message(self, f: function): return self.message()(f)
	@dispatch
	def message(self, filters=Filters.update, **kwargs): return self.handler(MessageHandler, filters, **kwargs)

	@dispatch
	def callback(self, f: function): return self.callback(rf"^{f.__name__}$")(f)
	@dispatch
	def callback(self, pattern, **kwargs): return self.handler(CallbackQueryHandler, pattern=pattern, **kwargs)

	@dispatch
	def command_unknown(self, f: function): return self.command_unknown()(f)
	@dispatch
	def command_unknown(self, filters=Filters.command, **kwargs): return self.handler(MessageHandler, filters, **kwargs)

	@property
	def bot(self):
		return self.updater.bot

class LogHandler(MessageHandler):
	def __init__(self, filters):
		super().__init__(filters, None)

	def check_update(self, update):
		if (super().check_update(update)): log(2, update)
		return False

if (__name__ == '__main__'): logstarted(); exit()
else: logimported()

# by Sdore, 2021
