"""注文の管理と記録"""

import csv
import os
from dataclasses import dataclass, field
from datetime import datetime

from menu import MenuItem

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "order_log.csv")
LOG_HEADER = ["日時", "伝票番号", "操作", "品名", "単価", "数量", "金額"]

MAX_QUANTITY = 99


@dataclass
class OrderLine:
    line_no: int
    item: MenuItem
    quantity: int

    @property
    def subtotal(self):
        return self.item.price * self.quantity


class OrderLogger:
    """注文・取消・会計を CSV に追記していく"""

    def __init__(self, path=LOG_FILE):
        self.path = path

    def write(self, slip_no, action, name="", price="", quantity="", amount=""):
        is_new = not os.path.exists(self.path)
        # Excel で文字化けしないよう BOM 付き UTF-8 で保存する
        with open(self.path, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if is_new:
                writer.writerow(LOG_HEADER)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([now, slip_no, action, name, price, quantity, amount])

    def read(self):
        """記録をすべて読み込む（ファイルが無ければ空）"""
        if not os.path.exists(self.path):
            return []
        with open(self.path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    def last_slip_no(self):
        """記録済みの最大伝票番号（無ければ 0）"""
        return max((slip.slip_no for slip in self.history()), default=0)

    def history(self):
        """記録を伝票ごとにまとめ、新しい順に返す"""
        slips = {}
        for row in self.read():
            try:
                slip_no = int(row["伝票番号"])
            except (KeyError, TypeError, ValueError):
                continue  # 壊れた行は読み飛ばす
            slip = slips.setdefault(slip_no, SlipHistory(slip_no))
            slip.rows.append(row)
        return sorted(slips.values(), key=lambda s: s.slip_no, reverse=True)


def _to_int(text):
    try:
        return int(text)
    except (TypeError, ValueError):
        return 0


@dataclass
class SlipHistory:
    """履歴表示用の 1 伝票分の記録"""
    slip_no: int
    rows: list = field(default_factory=list)

    @property
    def started_at(self):
        return self.rows[0]["日時"] if self.rows else ""

    @property
    def checkout_row(self):
        return next((r for r in self.rows if r.get("操作") == "会計"), None)

    @property
    def paid(self):
        return self.checkout_row is not None

    @property
    def total(self):
        if self.paid:
            return _to_int(self.checkout_row.get("金額"))
        # 未会計なら注文と取消を足し合わせた現時点の金額
        return sum(_to_int(r.get("金額")) for r in self.rows if r.get("操作") in ("注文", "取消"))


class Order:
    """1 伝票（1 組のお客様）分の注文"""

    def __init__(self, logger=None):
        self.logger = logger or OrderLogger()
        self.slip_no = self.logger.last_slip_no() + 1
        self.lines = []
        self._next_line_no = 1
        self.closed = False

    def add(self, item, quantity):
        if self.closed:
            raise RuntimeError("会計済みの伝票には追加できません")
        if not 1 <= quantity <= MAX_QUANTITY:
            raise ValueError(f"数量は 1〜{MAX_QUANTITY} で指定してください")
        line = OrderLine(self._next_line_no, item, quantity)
        self._next_line_no += 1
        self.lines.append(line)
        self.logger.write(self.slip_no, "注文", item.name, item.price, quantity, line.subtotal)
        return line

    def cancel(self, line_no):
        if self.closed:
            raise RuntimeError("会計後は取り消せません")
        for line in self.lines:
            if line.line_no == line_no:
                self.lines.remove(line)
                self.logger.write(self.slip_no, "取消", line.item.name, line.item.price,
                                  line.quantity, -line.subtotal)
                return line
        raise KeyError(line_no)

    @property
    def total(self):
        return sum(line.subtotal for line in self.lines)

    def checkout(self):
        if self.closed:
            raise RuntimeError("この伝票は会計済みです")
        if not self.lines:
            raise ValueError("注文がありません")
        self.closed = True
        self.logger.write(self.slip_no, "会計", amount=self.total)
        return self.total
