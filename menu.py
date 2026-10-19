"""店名とメニューの定義"""

from dataclasses import dataclass, field

STORE_NAME = "洋食レストラン ひだまり亭"

CATEGORIES = ["前菜", "メイン", "ご飯・パスタ", "ドリンク", "デザート"]

# 表示義務のある特定原材料 8 品目
ALLERGENS = ["卵", "乳", "小麦", "えび", "かに", "そば", "落花生", "くるみ"]


@dataclass(frozen=True)
class MenuItem:
    id: int
    name: str
    category: str
    price: int  # 税込価格（円）
    # おすすめ判定用のタグ
    #   kids: 子ども向け / hearty: ボリューム / light: あっさり・軽め
    #   healthy: ヘルシー / sweet: 甘い / alcohol: アルコール（20歳以上のみ）
    tags: frozenset = field(default_factory=frozenset)
    allergens: frozenset = field(default_factory=frozenset)

    def allergens_in(self, avoid):
        """avoid のうちこの料理に含まれるものを ALLERGENS の順で返す"""
        return [a for a in ALLERGENS if a in self.allergens and a in avoid]

    @property
    def allergen_text(self):
        return "・".join(a for a in ALLERGENS if a in self.allergens) or "なし"


def _item(id, name, category, price, tags=(), allergens=()):
    unknown = set(allergens) - set(ALLERGENS)
    assert not unknown, f"未定義のアレルゲン: {unknown}"
    return MenuItem(id, name, category, price, frozenset(tags), frozenset(allergens))


MENU = [
    # 前菜
    _item(1, "シーザーサラダ", "前菜", 680, ("healthy", "light"), ("卵", "乳", "小麦")),
    _item(2, "コーンポタージュ", "前菜", 420, ("kids", "light"), ("乳", "小麦")),
    _item(3, "フライドポテト", "前菜", 450, ("kids", "hearty")),
    _item(4, "カプレーゼ", "前菜", 780, ("healthy", "light"), ("乳",)),
    _item(5, "エビとマッシュルームのアヒージョ", "前菜", 880, ("hearty",), ("えび", "小麦")),
    # メイン
    _item(6, "デミグラスハンバーグ", "メイン", 1380, ("kids", "hearty"), ("卵", "乳", "小麦")),
    _item(7, "国産牛サーロインステーキ 200g", "メイン", 2980, ("hearty",), ("小麦",)),
    _item(8, "若鶏のグリル ハーブソース", "メイン", 1280, ("healthy",), ("乳",)),
    _item(9, "白身魚のムニエル", "メイン", 1480, ("healthy", "light"), ("乳", "小麦")),
    _item(10, "エビフライ（3本）", "メイン", 1350, ("kids", "hearty"), ("えび", "卵", "小麦")),
    # ご飯・パスタ
    _item(11, "オムライス", "ご飯・パスタ", 1080, ("kids",), ("卵", "乳", "小麦")),
    _item(12, "カルボナーラ", "ご飯・パスタ", 1180, ("hearty",), ("卵", "乳", "小麦")),
    _item(13, "和風きのこパスタ", "ご飯・パスタ", 1050, ("healthy", "light"), ("小麦",)),
    _item(14, "ビーフカレー", "ご飯・パスタ", 980, ("kids", "hearty"), ("乳", "小麦")),
    _item(15, "シーフードドリア", "ご飯・パスタ", 1150, ("light",), ("えび", "かに", "乳", "小麦")),
    # ドリンク
    _item(16, "オレンジジュース", "ドリンク", 380, ("kids", "sweet")),
    _item(17, "ホットコーヒー", "ドリンク", 400, ("light",)),
    _item(18, "アイスティー", "ドリンク", 400, ("light",)),
    _item(19, "ウーロン茶", "ドリンク", 350, ("healthy", "light")),
    _item(20, "生ビール（中）", "ドリンク", 580, ("alcohol",), ("小麦",)),
    _item(21, "グラスワイン（赤・白）", "ドリンク", 650, ("alcohol",)),
    # デザート
    _item(22, "カスタードプリン", "デザート", 450, ("kids", "sweet"), ("卵", "乳")),
    _item(23, "ベイクドチーズケーキ", "デザート", 520, ("sweet",), ("卵", "乳", "小麦")),
    _item(24, "バニラアイス", "デザート", 380, ("kids", "sweet", "light"), ("卵", "乳")),
    _item(25, "抹茶パフェ くるみ添え", "デザート", 780, ("sweet", "hearty"), ("乳", "小麦", "くるみ")),
    _item(26, "フルーツヨーグルト", "デザート", 480, ("healthy", "light"), ("乳",)),
    _item(27, "フルーツシャーベット", "デザート", 420, ("kids", "sweet", "light")),
]

MENU_BY_ID = {item.id: item for item in MENU}


def items_in(category, avoid=()):
    """カテゴリのメニューを返す。None なら全品。avoid のアレルゲンを含む品は除く。"""
    return [
        item for item in MENU
        if (category is None or item.category == category) and not item.allergens_in(avoid)
    ]
