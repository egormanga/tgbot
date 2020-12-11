#!/usr/bin/python3
# tgbot

import telegram
from telegram import *
from telegram.ext import *
from telegram.error import *
from utils import *; logstart('tgbot')

class TGBot(Slots):
	""" Meant to be `@singleton'-ed. """

	token: None
	queue: ...
	updater: ...
	dispatcher: ...
	persistence: None
	proxy_url: None
	proxy_list_url = "http://spys.me/proxy.txt"

	def __init__(self, log_filters=None):
		if (not self.token): raise ValueError(f"{self.__name__}.token is unspecified.")
		if (self.proxy_url is ...): self.proxy_url = self.get_proxy()
		self.updater = Updater(token=self.token, persistence=self.persistence, request_kwargs={'proxy_url': self.proxy_url}, use_context=True)
		self.dispatcher = self.updater.dispatcher
		self.dispatcher.add_handler(LogHandler(log_filters))
		self.dispatcher.add_error_handler(self.error_callback)

	def run(self):
		self.start()
		self.idle()

	def start(self, **kwargs):
		self.queue = self.updater.start_polling(**kwargs)

	def idle(self, **kwargs):
		self.updater.idle(**kwargs)

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
					parseargs(kwargs, chat_id = (update.effective_chat or update.effective_user).id, message_id=message_id, text=text)
					msg = (context.bot.edit_message_text if (message_id is not None) else context.bot.send_message)(**kwargs)
					context.user_data['_last_message_id'] = msg.message_id
					return msg
				update.reply = reply
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

class LogHandler(MessageHandler):
	def __init__(self, filters):
		super().__init__(filters, None)

	def check_update(self, update):
		if (super().check_update(update)): log(2, update)
		return False

if (__name__ == '__main__'): logstarted(); exit()
else: logimported()

# by Sdore, 2020
