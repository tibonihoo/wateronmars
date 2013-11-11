# -*- coding: utf-8 -*-

import urllib

print "\xe7\xbb\xb4\xe5\x9f\xba\xe6\x96\xb0\xe9\x97\xbb\xef\xbc\x8c\xe8\x87\xaa\xe7\x94\xb1\xe7\x9a\x84\xe6\x96\xb0\xe9\x97\xbb\xe6\xba\x90"
print urllib.unquote_plus("http%3A%2F%2Fzh.wikinews.org%2Fwiki%2FWikinews%3A%25E9%25A6%2596%25E9%25A1%25B5")
print urllib.unquote_plus(unicode("%E9%A6%96%E9%A1%B5").encode("utf-8"))
