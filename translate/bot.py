# translate - A maubot plugin to translate words.
# Copyright (C) 2019 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging
from typing import Optional, Tuple, Type, Dict

from mautrix.util.config import BaseProxyConfig
from mautrix.types import RoomID, EventType, MessageType
from maubot import Plugin, MessageEvent
from maubot.handlers import command, event

logger = logging.getLogger(__name__)

from .provider import AbstractTranslationProvider
from .util import Config, LanguageCodePair, TranslationProviderError, AutoTranslateConfig

try:
    import langid
except ImportError:
    langid = None


class TranslatorBot(Plugin):
    translator: Optional[AbstractTranslationProvider]
    auto_translate: Dict[RoomID, list]
    config: Config

    async def start(self) -> None:
        await super().start()
        self.on_external_config_update()

    def on_external_config_update(self) -> None:
        self.translator = None
        self.config.load_and_update()
        self.auto_translate = self.config.load_auto_translate()
        try:
            self.translator = self.config.load_translator()
        except TranslationProviderError:
            self.log.exception("Error loading translator")

    @classmethod
    def get_config_class(cls) -> Type['BaseProxyConfig']:
        return Config

    @event.on(EventType.ROOM_MESSAGE)
    async def event_handler(self, evt: MessageEvent) -> None:
        if (langid is None or evt.content.msgtype != MessageType.TEXT
                or evt.sender == self.client.mxid):
            return
        try:
            atc = self.auto_translate[evt.room_id]
        except KeyError:
            return
        langs = []
        for pair in atc:
            # Only use the first two letters for langid
            langs.extend([lang[:2] for lang in pair])
        langs = set(langs)
        langid.set_languages(langs=langs)
        class Found(Exception): pass
        try:
            detected = langid.classify(evt.content.body)[0]
            try:
                for pair in atc:
                    for i, l in enumerate(pair):
                        if detected in l:
                            target = pair[(i+1)%2]
                            raise Found()
                logger.debug(f'{detected} not in language pairs: {atc}')
                return
            except Found:
                pass
        except Exception as e:
            logging.exception(e)
            return

        result = await self.translator.translate(evt.content.body, to_lang=target)
        await evt.reply(result.text)


    @command.new("translate", aliases=["tr"])
    @LanguageCodePair("language", required=False)
    @command.argument("text", pass_raw=True, required=False)
    async def command_handler(self, evt: MessageEvent, language: Optional[Tuple[str, str]],
                              text: str) -> None:
        if not language:
            await evt.reply("Usage: !translate [from] <to> [text or reply to message]")
            return
        if not self.config["response_reply"]:
            evt.disable_reply = True
        if not self.translator:
            self.log.warn("Translate command used, but translator not loaded")
            return
        if not text and evt.content.get_reply_to():
            reply_evt = await self.client.get_event(evt.room_id, evt.content.get_reply_to())
            text = reply_evt.content.body
        if not text:
            await evt.reply("Usage: !translate [from] <to> [text or reply to message]")
            return
        result = await self.translator.translate(text, to_lang=language[1], from_lang=language[0])
        await evt.reply(result.text)
