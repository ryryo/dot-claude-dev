---
description: Pythonコーディング規約。PEP 8準拠、型ヒント必須。
globs:
  - "**/*.py"
---

# Pythonコーディング規約

## 基本スタイル（PEP 8）

### インポート

```python
# 標準ライブラリ
import os
import sys
from typing import Optional, List

# サードパーティ
import requests
from pydantic import BaseModel

# ローカル
from app.models import User
from app.services import UserService
```

### 命名規則

| 要素 | 規則 | 例 |
|------|------|-----|
| クラス | PascalCase | `UserService` |
| 関数/変数 | snake_case | `get_user_by_id` |
| 定数 | SCREAMING_SNAKE | `MAX_RETRY_COUNT` |
| プライベート | _prefix | `_internal_method` |

## 型ヒント

### 基本的な型ヒント

```python
from typing import Optional, List, Dict, Union

def get_user(user_id: int) -> Optional[User]:
    """ユーザーをIDで取得する"""
    return db.query(User).filter(User.id == user_id).first()

def process_items(items: List[str]) -> Dict[str, int]:
    """アイテムを処理し、カウントを返す"""
    return {item: len(item) for item in items}
```

### Python 3.10+ 型ヒント

```python
def process(value: str | int | None) -> str | None:
    if value is None:
        return None
    return str(value)
```

### Pydanticモデル

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: int | None = None

    class Config:
        str_strip_whitespace = True
```

## 関数・クラス

### 関数

```python
def calculate_total(
    items: List[Item],
    *,
    discount: float = 0.0,
    tax_rate: float = 0.1,
) -> float:
    """
    アイテムの合計金額を計算する。

    Args:
        items: 計算対象のアイテムリスト
        discount: 割引率（0.0-1.0）
        tax_rate: 税率

    Returns:
        税込み合計金額

    Raises:
        ValueError: 割引率が範囲外の場合
    """
    if not 0 <= discount <= 1:
        raise ValueError("Discount must be between 0 and 1")

    subtotal = sum(item.price for item in items)
    discounted = subtotal * (1 - discount)
    return discounted * (1 + tax_rate)
```

### データクラス

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def display_name(self) -> str:
        return f"{self.name} <{self.email}>"
```

## エラーハンドリング

### カスタム例外

```python
class ValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__("Validation failed")

# 使用例
try:
    validate_user(data)
except ValidationError as e:
    for field, error in e.errors.items():
        print(f"{field}: {error}")
```

### Result パターン

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    success: bool
    value: T | None = None
    error: str | None = None

    @classmethod
    def ok(cls, value: T) -> 'Result[T]':
        return cls(success=True, value=value)

    @classmethod
    def fail(cls, error: str) -> 'Result[T]':
        return cls(success=False, error=error)
```

## 禁止事項

- ❌ `from module import *`
- ❌ 型ヒントなしの公開関数
- ❌ ミュータブルなデフォルト引数
- ❌ グローバル変数の変更

## 推奨事項

- ✅ f-string使用
- ✅ walrus演算子 `:=`（適切な場合）
- ✅ コンテキストマネージャ `with`
- ✅ リスト内包表記（適度に）
