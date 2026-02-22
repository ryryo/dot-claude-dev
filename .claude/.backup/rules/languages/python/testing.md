---
description: Pythonテスト規約。pytest使用。
globs:
  - "**/test_*.py"
  - "**/*_test.py"
---

# Pythonテスト規約

## テストフレームワーク

pytest を使用。

## テスト構造

### 基本構造

```python
import pytest
from app.services import UserService
from app.models import User

class TestUserService:
    """UserServiceのテスト"""

    def setup_method(self):
        """各テストの前に実行"""
        self.service = UserService()

    def test_find_by_id_returns_user(self):
        """IDでユーザーを取得できる"""
        # Given
        user_id = 1

        # When
        result = self.service.find_by_id(user_id)

        # Then
        assert result is not None
        assert result.id == user_id

    def test_find_by_id_returns_none_when_not_found(self):
        """存在しないIDではNoneを返す"""
        result = self.service.find_by_id(999)
        assert result is None
```

### 関数ベース

```python
def test_calculate_total():
    """合計金額を計算する"""
    items = [Item(price=100), Item(price=200)]

    result = calculate_total(items)

    assert result == 300

def test_calculate_total_with_discount():
    """割引適用後の合計を計算する"""
    items = [Item(price=100)]

    result = calculate_total(items, discount=0.1)

    assert result == 99  # 100 * 0.9 * 1.1
```

## フィクスチャ

```python
import pytest

@pytest.fixture
def user():
    """テスト用ユーザー"""
    return User(id=1, name="John", email="john@example.com")

@pytest.fixture
def mock_repository(mocker):
    """モックリポジトリ"""
    return mocker.Mock(spec=UserRepository)

def test_with_fixtures(user, mock_repository):
    mock_repository.find.return_value = user
    service = UserService(mock_repository)

    result = service.find_by_id(1)

    assert result == user
```

## パラメータ化

```python
@pytest.mark.parametrize("email,expected", [
    ("user@example.com", True),
    ("invalid", False),
    ("", False),
    (None, False),
])
def test_validate_email(email, expected):
    result = validate_email(email)
    assert result == expected

@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

## モック

```python
def test_fetch_user(mocker):
    """APIからユーザーを取得"""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"id": 1, "name": "John"}
    mocker.patch("requests.get", return_value=mock_response)

    result = fetch_user(1)

    assert result["name"] == "John"

def test_with_mock_repository(mocker):
    """リポジトリをモック"""
    mock_repo = mocker.Mock(spec=UserRepository)
    mock_repo.find.return_value = User(id=1, name="John")

    service = UserService(mock_repo)
    result = service.find_by_id(1)

    mock_repo.find.assert_called_once_with(1)
    assert result.name == "John"
```

## 例外テスト

```python
def test_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        validate_user({"email": "invalid"})

    assert "email" in exc_info.value.errors

def test_raises_with_message():
    with pytest.raises(ValueError, match="must be positive"):
        process_negative(-1)
```

## 非同期テスト

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch():
    result = await async_fetch_user(1)
    assert result is not None
```

## 禁止事項

- ❌ テスト間の状態共有
- ❌ 外部サービスへの実際の接続
- ❌ 順序依存のテスト
- ❌ time.sleep()の使用

## 推奨事項

- ✅ describe形式の命名（pytest-describe）
- ✅ フィクスチャの活用
- ✅ conftest.pyで共通フィクスチャ
- ✅ pytest-covでカバレッジ測定
