#!/usr/bin/python3
# tgbot

import telegram
from telegram import *
from telegram.ext import *
from telegram.error import *
from utils import *; logstart('tgbot')

class TGBot(metaclass=SlotsMeta):
	""" Meant to be `@singleton'-ed. """

	token: ...
	updater: ...
	dispatcher: ...
	persistence: None
	proxy_url: None
	proxy_list_url = "http://spys.me/proxy.txt"

	def __init__(self, log_filters=None):
		if (self.proxy_url is ...): self.proxy_url = self.get_proxy()
		self.updater = Updater(token=self.token, persistence=self.persistence, request_kwargs={'proxy_url': self.proxy_url}, use_context=True)
		self.dispatcher = self.updater.dispatcher
		self.dispatcher.add_handler(LogHandler(log_filters))
		self.dispatcher.add_error_handler(self.error_callback)

	def run(self):
		self.updater.start_polling()

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

	def handler(self, handler_, *args, **kwargs):
		@funcdecorator
		def decorator(f):
			def decorated(update, context):
				scope = AttrProxy(update, context)
				globals = f.__globals__
				globals.update(dict(scope))
				#globals['bot'] = self
				globals['reply'] = lambda text, **kwargs: context.bot.send_message(chat_id=update.message.chat_id, text=text, **kwargs)
				try: return f(update, context)
				finally:
					for i in scope:
						globals.pop(i, None)
			handler = handler_(*args, callback=decorated, **kwargs)
			self.dispatcher.add_handler(handler)
			return decorated
		return decorator

	@dispatch
	def command(self, f: function): return self.command(f.__name__)(f)
	@dispatch
	def command(self, cmd: str, **kwargs): return self.handler(CommandHandler, cmd[1:] if (cmd.startswith('/')) else cmd, **kwargs)
	@dispatch
	def message(self, f: function): return self.message()
	@dispatch
	def message(self, filters=Filters.update, **kwargs): return self.handler(MessageHandler, filters, **kwargs)

class LogHandler(MessageHandler):
	def __init__(self, filters):
		super().__init__(filters, None)

	def check_update(self, update):
		if (super().check_update(update)): log(2, update)
		return False

if (__name__ == '__main__'): logstarted(); exit()
else: logimported()

# by Sdore, 2020
