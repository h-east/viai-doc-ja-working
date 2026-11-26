# 新規翻訳の道具

既存の訳を直すのではなく、`en/{name}.txt` から `doc/{name}.jax` を訳し
なおす時に使う。

## 手順

1. 下書き `{name}.draft` を書く (書式は下記)。AI エージェントに書かせる
   時の指示は `TRANSLATE.md`。
2. `build.py` で `.jax` を組み立てる。段落は autofmt で `gq` される。

       VIMPROG=vim AUTOFMT=~/.vim/plugged/autofmt \
           tools/retranslate/build.py en/{name}.txt {name}.draft doc/{name}.jax

   `VIMPROG` は実行する Vim、`AUTOFMT` は autofmt プラグインのディレク
   トリ (`packadd autofmt` で読める場合は不要)。ViAI を使う場合は
   `VIM` と `VIMRUNTIME` も設定する。
3. `check.py` と `make check` で確かめる。

       tools/retranslate/check.py en/{name}.txt doc/{name}.jax

   - 行末で揃えたタグの桁が原文と違う行
   - 79 桁を超える行 (表の行は 1 行のままでよい)
   - `"` または `` ` `` が奇数個の行 (囲まれた部分の途中で改行して
     いるかもしれない。文中の `'"'` などでも出るので目で見る)
4. 点検する。AI エージェントに点検させる時の指示は `REVIEW.md`。直す
   時は下書きを直して 2. からやりなおす。

## 下書きの書式

1 行が次のどれか 1 つ。

- `@N`、`@N-M`: `en/{name}.txt` の N 行目 (N〜M 行目) をそのまま写す。
  タグだけの行、コード例、区切り線、空行など、訳す語の無い行に使う。
- `=TEXT`: TEXT をそのまま出力する。見出し、表の行、訳したコード中の
  コメントなど、`gq` しない行に使う。空行は `=` だけの行。
- `§TEXT`: 1 段落を 1 行で書く。`gq` され、2 行目以降は TEXT の行頭の
  空白で字下げされる。`- ` で始まる箇条書きは 2 行目以降が `- ` の後
  ろにそろう。
- `§PREFIX§TEXT`: 項目名などの前置き (`\t"name"\t\t`、`1. ` など) が
  ある段落。`gq` の間だけ PREFIX を同じ幅の空白に置き換え、2 行目以降
  をその幅で字下げし、後で PREFIX を戻す。
- `#!...`: コメント。出力しない。

原文が文の終わりで改行している場合 (AGENTS.md の「改行位置」) は、そこ
で段落を分けて `§` 行を 2 つにする。
