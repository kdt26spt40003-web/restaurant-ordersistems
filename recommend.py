"""年齢・性別・気分からおすすめ料理を選ぶ"""

from menu import MENU

GENDERS = ["回答しない", "男性", "女性", "その他"]
MOODS = ["おまかせ", "がっつり", "あっさり", "甘いもの"]

MAX_AGE = 120


def parse_age(text):
    """年齢の入力文字列を検証する。

    戻り値は (年齢, エラーメッセージ)。正しければエラーは None、
    不正なら年齢は None。例外は投げない。
    """
    text = (text or "").strip()
    # 全角数字も受け付ける
    text = text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    if text == "":
        return None, "年齢を入力してください。"
    try:
        age = int(text)
    except ValueError:
        try:
            float(text)
        except ValueError:
            return None, f"「{text}」は数字ではありません。年齢は整数で入力してください。"
        return None, "年齢は小数ではなく整数で入力してください。"
    if age < 0:
        return None, "年齢に負の値は入力できません。"
    if age > MAX_AGE:
        return None, f"年齢は 0〜{MAX_AGE} の範囲で入力してください。"
    return age, None


def _score(item, age, gender, mood):
    tags = item.tags
    score = 0
    if age <= 12:
        score += 3 * ("kids" in tags) + ("sweet" in tags)
    elif age <= 19:
        score += 2 * ("hearty" in tags) + ("kids" in tags)
    elif age <= 59:
        score += ("hearty" in tags) + ("healthy" in tags) + 2 * ("alcohol" in tags)
    else:
        score += 2 * ("light" in tags) + 2 * ("healthy" in tags) - 2 * ("hearty" in tags)

    if gender == "男性":
        score += "hearty" in tags
    elif gender == "女性":
        score += ("healthy" in tags) + ("sweet" in tags)

    if mood == "がっつり":
        score += 3 * ("hearty" in tags)
    elif mood == "あっさり":
        score += 3 * ("light" in tags) - 2 * ("hearty" in tags)
    elif mood == "甘いもの":
        score += 3 * ("sweet" in tags)
    return score


# おすすめを 1 品ずつ選ぶ枠
_SLOTS = [
    ("前菜", ["前菜"]),
    ("お食事", ["メイン", "ご飯・パスタ"]),
    ("ドリンク", ["ドリンク"]),
    ("デザート", ["デザート"]),
]


def recommend(age, gender="回答しない", mood="おまかせ", avoid=()):
    """枠ごとのおすすめを [(枠名, MenuItem, 理由), ...] で返す。

    avoid に指定したアレルゲンを含む料理は選ばない。
    条件に合う料理が無い枠は結果に含めない。
    """
    result = []
    for slot, categories in _SLOTS:
        candidates = [
            item for item in MENU
            if item.category in categories
            and not ("alcohol" in item.tags and age < 20)  # 20 歳未満に酒類は出さない
            and not item.allergens_in(avoid)
        ]
        if not candidates:
            continue
        best = max(candidates, key=lambda item: (_score(item, age, gender, mood), -item.id))
        result.append((slot, best, _reason(best, age, mood)))
    return result


def _reason(item, age, mood):
    tags = item.tags
    if "alcohol" in tags:
        return "お料理と一緒にどうぞ"
    if age <= 12 and "kids" in tags:
        return "お子さまに人気"
    if mood == "がっつり" and "hearty" in tags:
        return "ボリューム満点"
    if mood == "甘いもの" and "sweet" in tags:
        return "甘いもの好きの方に"
    if "light" in tags and (mood == "あっさり" or age >= 60):
        return "あっさり軽め"
    if "healthy" in tags:
        return "ヘルシー"
    if "hearty" in tags:
        return "食べごたえあり"
    if "sweet" in tags:
        return "やさしい甘さ"
    return "当店の定番"
