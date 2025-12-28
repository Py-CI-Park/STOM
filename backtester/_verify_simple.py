# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from backtester.back_static import GetDerivedMetricsDocumentation

docs = GetDerivedMetricsDocumentation()
key = '당일거래대금_매수매도_비율_ML'

print('Documentation 존재:', key in docs)
if key in docs:
    doc = docs[key]
    print('desc:', doc.get('desc', 'N/A'))
    print('unit:', doc.get('unit', 'N/A'))
    print('note:', doc.get('note', 'N/A'))
