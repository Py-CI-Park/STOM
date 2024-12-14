try:
    from numba import njit

    @njit
    def GetKiwoomPgSgSp(bg, cg):
        gbfee = bg * 0.00015
        gsfee = cg * 0.00015
        gtexs = cg * 0.002
        bfee = gbfee - gbfee % 10
        sfee = gsfee - gsfee % 10
        texs = gtexs - gtexs % 1
        pg = int(cg - texs - bfee - sfee)
        sg = int(round(pg - bg))
        sp = round(sg / bg * 100, 2)
        return pg, sg, sp


    @njit
    def GetUpbitPgSgSp(bg, cg):
        bfee = bg * 0.0005
        sfee = cg * 0.0005
        pg = int(round(cg - bfee - sfee))
        sg = int(round(pg - bg))
        sp = round(sg / bg * 100, 2)
        return pg, sg, sp


    @njit
    def GetBinanceLongPgSgSp(bg, cg, market1, market2):
        bfee = bg * (0.0004 if market1 else 0.0002)
        sfee = (cg - bfee) * (0.0004 if market2 else 0.0002)
        pg = round(cg - bfee - sfee, 4)
        sg = round(pg - bg, 4)
        sp = round(sg / bg * 100, 2)
        return pg, sg, sp


    @njit
    def GetBinanceShortPgSgSp(bg, cg, market1, market2):
        bfee = bg * (0.0004 if market1 else 0.0002)
        sfee = (cg - bfee) * (0.0004 if market2 else 0.0002)
        pg = round(bg + bg - cg - bfee - sfee, 4)
        sg = round(pg - bg, 4)
        sp = round(sg / bg * 100, 2)
        return pg, sg, sp


    @njit
    def GetVIPrice(kosd, std_price, index):
        uvi = int(std_price * 1.1)
        x = GetHogaunit(kosd, uvi, index)
        if uvi % x != 0:
            uvi += x - uvi % x
        dvi = int(std_price * 0.9)
        y = GetHogaunit(kosd, dvi, index)
        if dvi % y != 0:
            dvi -= dvi % y
        return int(uvi), int(dvi), int(x)


    @njit
    def GetSangHahanga(kosd, predayclose, index):
        uplimitprice = int(predayclose * 1.30)
        x = GetHogaunit(kosd, uplimitprice, index)
        if uplimitprice % x != 0:
            uplimitprice -= uplimitprice % x
        downlimitprice = int(predayclose * 0.70)
        x = GetHogaunit(kosd, downlimitprice, index)
        if downlimitprice % x != 0:
            downlimitprice += x - downlimitprice % x
        return int(uplimitprice), int(downlimitprice)


    @njit
    def GetUvilower5(uvi, hogaunit, index):
        upper5 = uvi - hogaunit * 5
        if GetHogaunit(True, upper5, index) != hogaunit:
            k = 0
            hogaunit2 = 0
            for i in [1, 2, 3, 4, 5]:
                hogaunit_ = GetHogaunit(True, uvi - hogaunit * i, index)
                if hogaunit_ != hogaunit:
                    hogaunit2 = hogaunit_
                    break
                k += 1
            upper5 = uvi - hogaunit * k - hogaunit2 * (5 - k)
        return upper5


    @njit
    def GetHogaunit(kosd, price, index):
        if index < 20230125000000:
            if price < 1000:
                x = 1
            elif price < 5000:
                x = 5
            elif price < 10000:
                x = 10
            elif price < 50000:
                x = 50
            elif kosd:
                x = 100
            elif price < 100000:
                x = 100
            elif price < 500000:
                x = 500
            else:
                x = 1000
        else:
            if price < 2000:
                x = 1
            elif price < 5000:
                x = 5
            elif price < 20000:
                x = 10
            elif price < 50000:
                x = 50
            elif price < 200000:
                x = 100
            elif price < 500000:
                x = 500
            else:
                x = 1000
        return x
except:
    def GetKiwoomPgSgSp(bg, cg):
        gbfee = bg * 0.00015
        gsfee = cg * 0.00015
        gtexs = cg * 0.002
        bfee = gbfee - gbfee % 10
        sfee = gsfee - gsfee % 10
        texs = gtexs - gtexs % 1
        pg = int(cg - texs - bfee - sfee)
        sg = int(round(pg - bg))
        sp = round(sg / bg * 100, 2)
        return pg, sg, sp


    def GetUpbitPgSgSp(bg, cg):
        bfee = bg * 0.0005
        sfee = cg * 0.0005
        pg = int(round(cg - bfee - sfee))
        sg = int(round(pg - bg))
        sp = round(sg / bg * 100, 2)
        return pg, sg, sp


    def GetBinanceLongPgSgSp(bg, cg, market1, market2):
        bfee = bg * (0.0004 if market1 else 0.0002)
        sfee = (cg - bfee) * (0.0004 if market2 else 0.0002)
        pg = round(cg - bfee - sfee, 4)
        sg = round(pg - bg, 4)
        sp = round(sg / bg * 100, 2)
        return pg, sg, sp


    def GetBinanceShortPgSgSp(bg, cg, market1, market2):
        bfee = bg * (0.0004 if market1 else 0.0002)
        sfee = (cg - bfee) * (0.0004 if market2 else 0.0002)
        pg = round(bg + bg - cg - bfee - sfee, 4)
        sg = round(pg - bg, 4)
        sp = round(sg / bg * 100, 2)
        return pg, sg, sp


    def GetVIPrice(kosd, std_price, index):
        uvi = int(std_price * 1.1)
        x = GetHogaunit(kosd, uvi, index)
        if uvi % x != 0:
            uvi += x - uvi % x
        dvi = int(std_price * 0.9)
        y = GetHogaunit(kosd, dvi, index)
        if dvi % y != 0:
            dvi -= dvi % y
        return int(uvi), int(dvi), int(x)


    def GetSangHahanga(kosd, predayclose, index):
        uplimitprice = int(predayclose * 1.30)
        x = GetHogaunit(kosd, uplimitprice, index)
        if uplimitprice % x != 0:
            uplimitprice -= uplimitprice % x
        downlimitprice = int(predayclose * 0.70)
        x = GetHogaunit(kosd, downlimitprice, index)
        if downlimitprice % x != 0:
            downlimitprice += x - downlimitprice % x
        return int(uplimitprice), int(downlimitprice)


    def GetUvilower5(uvi, hogaunit, index):
        upper5 = uvi - hogaunit * 5
        if GetHogaunit(True, upper5, index) != hogaunit:
            k = 0
            hogaunit2 = 0
            for i in [1, 2, 3, 4, 5]:
                hogaunit_ = GetHogaunit(True, uvi - hogaunit * i, index)
                if hogaunit_ != hogaunit:
                    hogaunit2 = hogaunit_
                    break
                k += 1
            upper5 = uvi - hogaunit * k - hogaunit2 * (5 - k)
        return upper5


    def GetHogaunit(kosd, price, index):
        if index < 20230125000000:
            if price < 1000:
                x = 1
            elif price < 5000:
                x = 5
            elif price < 10000:
                x = 10
            elif price < 50000:
                x = 50
            elif kosd:
                x = 100
            elif price < 100000:
                x = 100
            elif price < 500000:
                x = 500
            else:
                x = 1000
        else:
            if price < 2000:
                x = 1
            elif price < 5000:
                x = 5
            elif price < 20000:
                x = 10
            elif price < 50000:
                x = 50
            elif price < 200000:
                x = 100
            elif price < 500000:
                x = 500
            else:
                x = 1000
        return x
