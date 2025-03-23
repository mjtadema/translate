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
from functools import partial
from typing import Dict
import asyncio

import deepl

from . import AbstractTranslationProvider, Result

logger = logging.getLogger(__name__)


class DeepLTranslate(AbstractTranslationProvider):
    supported_languages = {
        'ar': 'Arabic',
        'bg': 'Bulgarian',
        'cs': 'Czech',
        'da': 'Danish',
        'de': 'German',
        'el': 'Greek',
        'en-gb': 'English (British)',
        'en-us': 'English (American)',
        'es': 'Spanish',
        'et': 'Estonian',
        'fi': 'Finnish',
        'fr': 'French',
        'hu': 'Hungarian',
        'id': 'Indonesian',
        'it': 'Italian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'lt': 'Lithuanian',
        'lv': 'Latvian',
        'nb': 'Norwegian Bokmål',
        'nl': 'Dutch',
        'pl': 'Polish',
        'pt-br': 'Portuguese (Brazilian)',
        'pt-pt': 'Portuguese (all Portuguese variants excluding Brazilian Portuguese)',
        'ro': 'Romanian',
        'ru': 'Russian',
        'sk': 'Slovak',
        'sl': 'Slovenian',
        'sv': 'Swedish',
        'tr': 'Turkish',
        'uk': 'Ukrainian',
        'zh-hans': 'Chinese (simplified)',
        'zh-hant': 'Chinese (traditional)'
    }

    def __init__(self, args: Dict) -> None:
        try:
            api_key = args.pop('api_key')
        except KeyError as e:
            logger.critical("deepl backend requires an api_key to be provided in args")
            logger.exception(e)
            raise e
        self.translator = deepl.Translator(api_key)
        super().__init__(args)

    async def translate(self, text: str, to_lang: str, from_lang: str = 'auto') -> Result:
        if from_lang == 'auto':
            from_lang = None
        loop = asyncio.get_event_loop()
        translate_text = partial(self.translator.translate_text, text, target_lang=to_lang, source_lang=from_lang)
        result = await loop.run_in_executor(None, translate_text)
        return Result(text=result.text, source_language=from_lang if not from_lang is None else result.detected_source_lang)

    def is_supported_language(self, code: str) -> bool:
        return code.lower() in self.supported_languages.keys()

    def get_language_name(self, code: str) -> str:
        return self.supported_languages.get(code.lower(), 'not supported')


make_translation_provider = DeepLTranslate
