#!/bin/sh
# index.html 안의 모듈 스크립트 문법 검사
python3 -c "
import re,sys;s=open(sys.argv[1],encoding='utf-8').read()
open('/tmp/_df_check.mjs','w').write(re.findall(r'<script type=\"module\">(.*?)</script>',s,re.S)[0])" "${1:-index.html}" && node --check /tmp/_df_check.mjs && echo SYNTAX_OK
