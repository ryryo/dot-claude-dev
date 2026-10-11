# 架空の再開処理の不具合

中断したimporterは永続化した最後のrecordの次から再開し、重複させない。

record 42とcheckpoint `42` を保存した後の再起動で、42を再度取り込む。`resumeFromCheckpoint()` が保存したindexをそのまま返し、loopがそこから始まる。`resume.test.ts` には安価なcheckpointと出力配列のfixtureがある。本実装はまだ変更していない。
