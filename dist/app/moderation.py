# moderation.py

import re

# ИЗМЕНЕНИЕ: Универсальные замены "leetspeak" (цифры на буквы)
LEETSPEAK_REPLACEMENTS = {
    '0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's', '6': 'b', '7': 't', '9': 'g'
}

# ИЗМЕНЕНИЕ: Специальные замены похожих латинских букв на кириллические
CYRILLIC_REPLACEMENTS = {
    'a': 'а', 'b': 'в', 'c': 'с', 'e': 'е', 'k': 'к', 'm': 'м', 
    'h': 'н', 'o': 'о', 'p': 'р', 't': 'т', 'y': 'у', 'x': 'х',
    'u': 'и', 'z': 'z' # 'z' добавлена для полноты
}

# Словари со стоп-словами
STOP_WORDS = {
    'ru': {
        'мат', 'ругательство', 'оскорбление', 'обман', 'мошенник', 
        'пидор', 'хуй', 'сука', 'блять', 'шлюха', 'ублюдок', 'блядь', 
        'угроза', 'насилие', 'дерьмо', 'гавно', 'лох', 'чмо', 'еблан'
    },
    'en': {
        'badword', 'curse', 'insult', 'scam', 'fraud', 'fuck', 'shit', 
        'bitch', 'asshole', 'bastard', 'suck', 'whore', 'cunt', 'dick', 
        'hate', 'kill', 'nigger', 'faggot', 'spam', 'deception'
    },
    'pl': {
        'przekleństwo', 'obelga', 'wulgaryzm', 'oszustwo', 'kurwa', 
        'chuj', 'dupa', 'jebać', 'pierdol', 'kurew', 'szmata', 'huj', 
        'sukinsyn', 'debil', 'cholera'
    }
}


# ИЗМЕНЕНИЕ: Новая, более универсальная функция нормализации
def normalize_text(text: str, lang: str) -> str:
    """
    Приводит текст к "нормальной" форме для проверки.
    1. Применяет универсальные заменты (leetspeak).
    2. Для русского языка дополнительно заменяет похожие латинские буквы.
    """
    lower_text = text.lower()
    
    # Шаг 1: Универсальная замена цифр на буквы для всех языков
    for digit, char in LEETSPEAK_REPLACEMENTS.items():
        lower_text = lower_text.replace(digit, char)
    
    # Шаг 2: Дополнительная замена для русского языка
    if lang == 'ru':
        for lat, cyr in CYRILLIC_REPLACEMENTS.items():
            lower_text = lower_text.replace(lat, cyr)
            
    return lower_text


def check_text_for_stop_words(text: str, lang: str) -> bool:
    """
    Проверяет текст на наличие стоп-слов для данного языка.
    Нормализует текст перед проверкой.
    """
    if not text:
        return False
        
    # ИЗМЕНЕНИЕ: Применяем универсальную нормализацию для всех языков
    normalized_text = normalize_text(text, lang)
    
    # Очищаем от знаков препинания
    cleaned_text = re.sub(r'[^\w\s]', '', normalized_text)
    
    words_in_text = set(cleaned_text.split())
    stop_words_for_lang = STOP_WORDS.get(lang, set())

    # Проверяем, содержится ли какое-либо стоп-слово в словах из текста
    for word in words_in_text:
        for stop_word in stop_words_for_lang:
            if stop_word in word:
                return True
                
    return False