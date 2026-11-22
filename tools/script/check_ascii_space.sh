#! /bin/bash
#
# doc/*.jax の ASCII だけの行 (タグだけの行、コード例、区切り線など) で、
# 空白を除くと en/*.txt のある行と同じなのに、空白が違うものを検出する。
# 訳す文字の無い行は原文どおりに写すので、空白も原文と同じになる。
# 検出したら file:line 形式で報告して異常終了する。
#
# 引数で doc/*.jax のファイルを指定できる。省略時は全部を対象にする。
#
# 2026-11-23 h_east       : Create initial file.

set -u

targets=("$@")
if [ ${#targets[@]} -eq 0 ]; then
  targets=(doc/*.jax)
fi

rc=0
for jax in "${targets[@]}"; do
  txt=en/$(basename "${jax}" .jax).txt
  [ -f "${txt}" ] || continue
  LC_ALL=C awk -v jax="${jax}" '
    FNR == NR {
      line[$0] = 1
      key = $0; gsub(/[ \t]/, "", key)
      if (key != "") keys[key] = 1
      next
    }
    /[\200-\377]/ || ($0 in line) { next }
    {
      key = $0; gsub(/[ \t]/, "", key)
      if (key in keys) {
        printf "%s:%d: 空白が原文と違います\n", jax, FNR
        bad = 1
      }
    }
    END { exit bad }
  ' "${txt}" "${jax}" || rc=1
done
exit ${rc}
