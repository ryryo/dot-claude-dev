# 架空の認証差分

認証済みadminだけがworkspaceを削除できる目的。

```diff
- if (!user || user.role !== "admin") {
+ if (!user && user.role !== "admin") {
    return { status: 403 };
  }
  await deleteWorkspace(workspaceId);
```

テストは認証済みadminが削除できる一件だけ。未認証と非adminの確認はない。
