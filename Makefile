.PHONY: all check replace html clean

all:

check:
	nvcheck doc/*.jax
	vim -eu tools/maketags.vim
	tools/script/check_leading_space.sh
	tools/script/check_tag_diff.sh

replace:
	nvcheck -i doc/*.jax

VIAI_HELP_SYNTAX = https://raw.githubusercontent.com/viai-editor/viai/master/runtime/syntax/help.vim

html:
	rm -rf target/html target/runtime
	mkdir -p target/html/doc target/runtime/syntax
	curl -fsSL -o target/runtime/syntax/help.vim $(VIAI_HELP_SYNTAX)
	cp doc/*.jax target/html/doc
	-cd target/html/doc ; vim -eu ../../../tools/buildhtml.vim -c "qall!"

clean:
	rm -rf target
