
def get_label_text(coin, arry, xpoint, factor, hms):
    def cindex(number):
        return dict_stock[number] if not coin else dict_coin[number]

    dict_stock = {
        1: 45, 2: 46, 3: 47, 4: 48, 5: 1, 6: 51, 7: 52, 8: 53, 9: 7, 10: 19, 11: 58, 12: 14, 13: 15, 14: 5, 15: 20,
        16: 22, 17: 21, 18: 38, 19: 37, 20: 43, 21: 6, 22: 56, 23: 57, 24: 59, 25: 60, 26: 61, 27: 8, 28: 9, 29: 10,
        30: 11, 40: 44, 41: 62, 42: 63
    }
    dict_coin = {
        1: 36, 2: 37, 3: 38, 4: 39, 5: 1, 6: 42, 7: 43, 8: 44, 9: 7, 10: 10, 11: 49, 12: 8, 13: 9, 14: 5, 15: 11,
        16: 13, 17: 12, 18: 29, 19: 28, 20: 34, 21: 6, 22: 47, 23: 48, 24: 50, 25: 51, 40: 35, 41: 52, 42: 53,
        43: 54, 44: 55
    }

    jpd = 0
    dmj = 0
    jip = 0
    hjp = 0
    jdp = 0
    ema0060 = arry[xpoint, cindex(1)]
    ema0300 = arry[xpoint, cindex(2)]
    ema0600 = arry[xpoint, cindex(3)]
    ema1200 = arry[xpoint, cindex(4)]
    cc      = arry[xpoint, cindex(5)]
    ch      = arry[xpoint, cindex(9)]
    ach     = arry[xpoint, cindex(6)]
    hch     = arry[xpoint, cindex(7)]
    lch     = arry[xpoint, cindex(8)]
    sm      = arry[xpoint, cindex(10)]
    asm     = arry[xpoint, cindex(11)]
    bbc     = arry[xpoint, cindex(12)]
    sbc     = arry[xpoint, cindex(13)]
    per     = arry[xpoint, cindex(14)]
    hlp     = arry[xpoint, cindex(15)]
    tbj     = arry[xpoint, cindex(16)]
    tsj     = arry[xpoint, cindex(17)]
    b1j     = arry[xpoint, cindex(18)]
    s1j     = arry[xpoint, cindex(19)]
    jr5     = arry[xpoint, cindex(20)]
    dm      = arry[xpoint, cindex(21)]
    nsb     = arry[xpoint, cindex(22)]
    nss     = arry[xpoint, cindex(23)]
    prd     = arry[xpoint, cindex(24)]
    dmd     = arry[xpoint, cindex(25)]
    if not coin:
        jpd = arry[xpoint, cindex(26)]
        dmj = arry[xpoint, cindex(27)]
        jip = arry[xpoint, cindex(28)]
        hjp = arry[xpoint, cindex(29)]
        jdp = arry[xpoint, cindex(30)]

    text = ''
    if factor == '현재가':
        if coin:
            text = f"시간 {hms}\n" \
                   f"이평0060 {ema0060:,.8f}\n" \
                   f"이평0300 {ema0300:,.8f}\n" \
                   f"이평0600 {ema0600:,.8f}\n" \
                   f"이평1200 {ema1200:,.8f}\n" \
                   f"현재가       {cc:,.4f}"
        else:
            text = f"시간 {hms}\n" \
                   f"이평0060 {ema0060:,.3f}\n" \
                   f"이평0300 {ema0300:,.3f}\n" \
                   f"이평0600 {ema0600:,.3f}\n" \
                   f"이평1200 {ema1200:,.3f}\n" \
                   f"현재가       {cc:,.0f}"
    # f"BOLBU {arry[xpoint, 64]:,.2f}\n" \
    # f"BOLBL {arry[xpoint, 65]:,.2f}"
    # elif factor == 'MACD':
    #     text = f"MACDD {arry[xpoint, 66]:,.2f}\n" \
    #            f"MACDS {arry[xpoint, 67]:,.2f}\n" \
    #            f"MACDH {arry[xpoint, 68]:,.2f}"
    # elif factor == 'RSI':
    #     text = f"RSI {arry[xpoint, 69]:,.2f}"
    elif factor == '체결강도':
        text = f"체결강도        {ch:,.2f}\n" \
               f"체결강도평균 {ach:,.2f}\n" \
               f"최고체결강도 {hch:,.2f}\n" \
               f"최저체결강도 {lch:,.2f}"
    elif factor == '초당거래대금':
        text = f"초당거래대금        {sm:,.0f}\n" \
               f"초당거래대금평균 {asm:,.0f}"
    elif factor == '초당체결수량':
        if coin:
            text = f"초당매수수량 {bbc:,.8f}\n" \
                   f"초당매도수량 {sbc:,.8f}"
        else:
            text = f"초당매수수량 {bbc:,.0f}\n" \
                   f"초당매도수량 {sbc:,.0f}"
    elif factor == '등락율':
        text = f"등락율 {per:,.2f}%"
    elif factor == '고저평균대비등락율':
        text = f"고저평균등락율 {hlp:,.2f}%"
    elif factor == '호가총잔량':
        if coin:
            text = f"매도총잔량 {tsj:,.8f}\n" \
                   f"매수총잔량 {tbj:,.8f}"
        else:
            text = f"매도총잔량 {tsj:,.0f}\n" \
                   f"매수총잔량 {tbj:,.0f}"
    elif factor == '1호가잔량':
        if coin:
            text = f"매도1잔량 {s1j:,.8f}\n" \
                   f"매수1잔량 {b1j:,.8f}"
        else:
            text = f"매도1잔량 {s1j:,.0f}\n" \
                   f"매수1잔량 {b1j:,.0f}"
    elif factor == '5호가잔량합':
        if coin:
            text = f"5호가잔량합 {jr5:,.8f}"
        else:
            text = f"5호가잔량합 {jr5:,.0f}"
    elif factor == '당일거래대금':
        text = f"당일거래대금 {dm:,.0f}"
    elif factor == '누적초당매도수수량':
        if coin:
            text = f"누적초당매수수량 {nsb:,.8f}\n" \
                   f"누적초당매도수량 {nss:,.8f}"
        else:
            text = f"누적초당매수수량 {nsb:,.0f}\n" \
                   f"누적초당매도수량 {nss:,.0f}"
    elif factor == '등락율각도':
        text = f"등락율각도 {prd:,.2f}º"
    elif factor == '당일거래대금각도':
        text = f"당일거래대금각도 {dmd:,.2f}º"
    elif factor == '전일비각도':
        text = f"전일비각도 {jpd:,.2f}º"
    elif factor == '거래대금증감':
        text = f"거래대금증감 {dmj:,.2f}"
    elif factor == '전일비':
        text = f"전일비 {jip:,.2f}%"
    elif factor == '회전율':
        text = f"회전율 {hjp:,.2f}%"
    elif factor == '전일동시간비':
        text = f"전일동시간비 {jdp:,.2f}%"
    return text
