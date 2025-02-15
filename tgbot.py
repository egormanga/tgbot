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

	# public:
	token: None
	base_url: None
	base_file_url: None
	webhook_host: None
	webhook_port: None
	webhook_path: None
	webhook_url: None
	persistence: None
	proxy_url: None
	proxy_list_url: "http://spys.me/proxy.txt"

	# private:
	application: ...

	@init(webhook_host=..., webhook_port=..., webhook_path=..., webhook_url=...)
	def __init__(self, token=None, *, log_filters=None, **kwargs):
		if (token is not None): self.token = token

		if (not self.token): raise ValueError(f"{self.__class__.__name__}.token is unspecified.")
		if (self.proxy_url is ...): self.proxy_url = self.get_proxy()

		application = Application.builder()
		if (self.token is not None): application.token(self.token)
		if (self.persistence is not None): application.persistence(self.persistence)
		if (self.base_url is not None): application.base_url(self.base_url)
		if (self.base_file_url is not None): application.base_file_url(self.base_file_url)
		if (self.proxy_url is not None): application.get_updates_proxy(self.proxy_url)
		self.application = application.build(); del application

		self.application.add_handler(LogHandler(log_filters))
		self.application.add_error_handler(self.error_callback)

	def run(self, **kwargs):
		if (self.webhook_port is not None):
			self.application.run_webhook(
				listen=self.webhook_host,
				port=int(self.webhook_port),
				url_path=self.webhook_path,
				webhook_url=self.webhook_url,
				**kwargs
			)
		else:
			self.application.run_polling(**kwargs)

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

	async def error_callback(self, update, context):
		exception(context.error)

	def handler(self, handler, *args, group=telegram.ext._application.DEFAULT_GROUP, **kwargs):
		def decorator(f):
			self.application.add_handler(handler(*args, callback=f, **kwargs), group=group)
			return f
		return decorator

	@dispatch
	def command(self, f: function): return self.command(f.__name__)(f)
	@dispatch
	def command(self, cmd: str, **kwargs): return self.handler(CommandHandler, (cmd[1:] if (cmd.startswith('/')) else cmd), **kwargs)

	@dispatch
	def message(self, f: function): return self.message()(f)
	@dispatch
	def message(self, filters_=filters.ALL, group=telegram.ext._application.DEFAULT_GROUP, **kwargs): return self.handler(MessageHandler, filters=filters_, group=group, **kwargs)

	@dispatch
	def callback(self, f: function): return self.callback(rf"^{f.__name__}$")(f)
	@dispatch
	def callback(self, pattern, **kwargs): return self.handler(CallbackQueryHandler, pattern=pattern, **kwargs)

	@dispatch
	def command_unknown(self, f: function): return self.command_unknown()(f)
	@dispatch
	def command_unknown(self, filters_=filters.COMMAND, **kwargs): return self.handler(MessageHandler, filters=filters_, **kwargs)

	@property
	def bot(self):
		return self.application.bot


class LogHandler(MessageHandler):
	def __init__(self, filters_):
		super().__init__(filters_, None)

	def check_update(self, update):
		if (super().check_update(update)): log(2, update)
		return False


class ReplyTo(filters.REPLY.__class__):
	__slots__ = ('_to',)

	def __init__(self, to_):
		self._to = to_
		super().__init__(name = f"filters.ReplyTo({self._to!r})")

	def filter(self, message: Message) -> bool:
		return bool(super().filter(message) and message.reply_to_message.from_user == self._to)
filters.ReplyTo = ReplyTo


if (__name__ == '__main__'): logstarted(); exit()
else: logimported()

# by Sdore, 2020-25
#   www.sdore.me
