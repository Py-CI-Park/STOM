
                    # 매도시점 1 [ Sell Stage 1 ] - 매수가에서 protection_percent 빠지면 매도
                    if (((self.kiwoom.watch[condition_name][code]['buy']) - (self.kiwoom.watch[condition_name][code]['current'])) / self.kiwoom.watch[condition_name][code]['buy']) * 100 >= self.protection_percent and self.protection_percent >= 0:       # 2019.07.03 (수) 수정
                    # if (((self.kiwoom.watch[condition_name][code]['buy']) - (self.kiwoom.watch[condition_name][code]['current'])) / self.kiwoom.watch[condition_name][code]['buy']) * 100 >= self.protection_percent:       # 2019.07.02 (화) 수정
                    # if self.kiwoom.watch[condition_name][code]['current'] < self.kiwoom.watch[condition_name][code]['buy'] and (((self.kiwoom.watch[condition_name][code]['buy']) - (self.kiwoom.watch[condition_name][code]['current'])) / self.kiwoom.watch[condition_name][code]['buy']) * 100 >= self.protection_percent:
                        status = 3

                        tracker = True      # 2020.07.08 (수) 추가

                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_1_1_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_1_1_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_1_1_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_1_1_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 1-1 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 1-1 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 1-1 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)


                    elif abs((((self.kiwoom.watch[condition_name][code]['buy']) - (self.kiwoom.watch[condition_name][code]['current'])) / self.kiwoom.watch[condition_name][code]['buy'])) * 100 <= abs(self.protection_percent) and self.protection_percent <= 0:        # 2019.07.03 (수) 수정
                        status = 3

                        tracker = True      # 2020.07.08 (수) 추가

                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_1_2_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_1_2_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_1_2_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_1_2_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 1-2 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 1-2 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 1-2 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)


                    elif (((self.kiwoom.watch[condition_name][code]['buy']) - (self.kiwoom.watch[condition_name][code]['current'])) / self.kiwoom.watch[condition_name][code]['buy']) * 100 >= abs(self.protection_percent) and self.protection_percent <= 0:        # 2019.07.03 (수) 수정
                        status = 3

                        tracker = True      # 2020.07.08 (수) 추가

                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_1_3_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_1_3_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_1_3_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_1_3_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 1-3 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 1-3 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 1-3 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)



                    # 매도시점 2 [ Sell Stage 2 ] - 최고가 (매수가의 high_protection_percent 이상의 최고가) 에서 high_protection_percent 빠지면 매도 ( 매도시점 3 과 4 의 알고리즘으로 target_percent 도달 이후에는 매도시점 2 는 고려 안됨 )
                    if self.kiwoom.watch[condition_name][code]['high'] > int(self.kiwoom.watch[condition_name][code]['buy'] * self.high_protection_percent_factor) and (((self.kiwoom.watch[condition_name][code]['high']) - (self.kiwoom.watch[condition_name][code]['current'])) / self.kiwoom.watch[condition_name][code]['high']) * 100 >= self.high_protection_percent:
                        status = 3

                        tracker = True      # 2020.07.08 (수) 추가

                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_2_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_2_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_2_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_2_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 2 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 2 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 2 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)



                    # 매도시점 3 [ Sell Stage 3 ] - 매수가에서 target_percent 수익 이상에서 조건부 매도
                    if self.kiwoom.watch[condition_name][code]['earning_rate'] >= self.target_percent:
                        if not self.kiwoom.watch[condition_name][code]['target_status'] or self.kiwoom.watch[condition_name][code]['target_status'] == '목표수익미도달':
                            self.kiwoom.watch[condition_name][code]['target_status'] = '목표수익도달'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - 목표수익도달' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)

                        if self.direct_sell == True:        # 2019.06.28 (금) 추가
                            status = 3

                            tracker = True      # 2020.07.08 (수) 추가

                            # 2020.07.06 (월) 추가 및 수정
                            current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                            # current_time = current.time()

                            check_time = str(current.hour) + str(current.minute)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage_3_1_check_time_list']:
                                self.kiwoom.watch[condition_name][code]['sell_stage_3_1_check_time_list'] = []

                            if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_3_1_check_time_list']).intersection(set([check_time]))) == 0:
                                self.kiwoom.watch[condition_name][code]['sell_stage_3_1_check_time_list'].append(check_time)

                                if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 3-1 ]'
                                else:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 3-1 ]'

                                text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 3-1 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                                self.kiwoom.print_log(text=text)

                        if rising_trend == False and (((self.kiwoom.watch[condition_name][code]['high']) - (self.kiwoom.watch[condition_name][code]['current'])) / self.kiwoom.watch[condition_name][code]['high']) * 100 >= self.second_high_protection_percent:
                            status = 3

                            tracker = True      # 2020.07.08 (수) 추가

                            # 2020.07.06 (월) 추가 및 수정
                            current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                            # current_time = current.time()

                            check_time = str(current.hour) + str(current.minute)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage_3_2_check_time_list']:
                                self.kiwoom.watch[condition_name][code]['sell_stage_3_2_check_time_list'] = []

                            if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_3_2_check_time_list']).intersection(set([check_time]))) == 0:
                                self.kiwoom.watch[condition_name][code]['sell_stage_3_2_check_time_list'].append(check_time)

                                if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 3-2 ]'
                                else:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 3-2 ]'

                                text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 3-2 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                                self.kiwoom.print_log(text=text)

                    else:
                        if not self.kiwoom.watch[condition_name][code]['target_status']:
                            self.kiwoom.watch[condition_name][code]['target_status'] = '목표수익미도달'
                        else:
                            self.kiwoom.watch[condition_name][code]['target_status'] = self.kiwoom.watch[condition_name][code]['target_status']


                    # 매도시점 4 [ Sell Stage 4 ] - 목표수익도달 이후 고가에서 일정 비율 내려오면 매도
                    if self.kiwoom.watch[condition_name][code]['target_status'] == '목표수익도달' and (((self.kiwoom.watch[condition_name][code]['high']) - (self.kiwoom.watch[condition_name][code]['current'])) / self.kiwoom.watch[condition_name][code]['high']) * 100 >= self.second_high_protection_percent:
                        status = 3

                        tracker = True      # 2020.07.08 (수) 추가

                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_4_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_4_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_4_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_4_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 4 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 4 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 4 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)


                    # 매도시점 5 [ Sell Stage 5 ] - 매수가에서 target_percent 수익 이상에서 조건부 매도 못하고 target_percent 수익 밑으로 내려 오면 매도
                    if self.kiwoom.watch[condition_name][code]['earning_rate'] < (self.target_percent - self.target_percent_damper) and self.kiwoom.watch[condition_name][code]['target_status'] == '목표수익도달':
                        status = 3

                        tracker = True      # 2020.07.08 (수) 추가

                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_5_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_5_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_5_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_5_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 5 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 5 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 5 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)


                    # 2019.08.03 (토) Sell Stage 6 => 6-1, 7 => 6-2 로 수정 및 if 문 합병
                    # 매도시점 6 [ Sell Stage 6 ] - TBD
                    if self.second_target == True and self.kiwoom.watch[condition_name][code]['high_earning_rate'] >= self.second_target_percent and self.kiwoom.watch[condition_name][code]['earning_rate'] <= self.second_target_sell_percent:        # 2019.08.03 (토) 수정
                        status = 3

                        tracker = True      # 2020.07.08 (수) 추가

                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_6_1_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_6_1_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_6_1_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_6_1_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 6-1 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 6-1 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 6-1 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)


                    elif self.third_target == True and self.kiwoom.watch[condition_name][code]['high_earning_rate'] >= self.third_target_percent and self.kiwoom.watch[condition_name][code]['earning_rate'] <= self.third_target_sell_percent:      # 2019.07.09 (화) 수정      # 2019.08.03 (토) 수정
                    # if self.kiwoom.watch[condition_name][code]['high_earning_rate'] >= 1.5 and self.kiwoom.watch[condition_name][code]['earning_rate'] <= 0.5:
                        status = 3

                        tracker = True      # 2020.07.08 (수) 추가

                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_6_2_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_6_2_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_6_2_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_6_2_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 6-2 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 6-2 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 6-2 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)


                    # 매도시점 7 [ Sell Stage 7 ] - 부분 매도, TBD
                    if self.partial_sell == True and self.first_partial_sell == True and self.kiwoom.watch[condition_name][code]['first_partial_sell_end'] == False and self.kiwoom.watch[condition_name][code]['earning_rate'] >= self.first_partial_sell_target_percent:     # 2019.08.03 (토) 추가

                        self.kiwoom.watch[condition_name][code]['first_partial_sell_stock_number'] = int(self.kiwoom.watch[condition_name][code]['stock_number'] * self.first_partial_sell_ratio)

                        # if self.kiwoom.watch[condition_name][code]['first_partial_sell_stock_number'] == 0:
                        #     self.kiwoom.watch[condition_name][code]['first_partial_sell_stock_number'] = 1

                        self.kiwoom.watch[condition_name][code]['left_stock_number'] = self.kiwoom.watch[condition_name][code]['stock_number'] - self.kiwoom.watch[condition_name][code]['first_partial_sell_stock_number']


                        """
                        self.kiwoom.log_msg += '[매도] 조건명: %s, 종목명: %s, 종목코드: %s, 매수가: %s, 매수 등락률: %s, 매수 거래량: %s, 매수 전일대비거래량비율: %s, 매수 체결강도: %s, 매수시간: %s, 고가: %s, 고가 등락률: %s, 고가 거래량: %s, 고가 전일대비거래량비율: %s, 고가 체결강도: %s, 매도가: %s, 매도 등락률: %s, 매도 거래량: %s, 매도 전일대비거래량비율: %s, 매도 체결강도: %s, 매도시간: %s, 수익률: %s' % (
                        condition_name, self.kiwoom.watch[condition_name][code]['stock_name'], code,
                        self.kiwoom.watch[condition_name][code]['buy'],
                        self.kiwoom.watch[condition_name][code]['buy_price_rate'],
                        self.kiwoom.watch[condition_name][code]['buy_volume'],
                        self.kiwoom.watch[condition_name][code]['buy_volume_rate'],
                        self.kiwoom.watch[condition_name][code]['buy_trade_power'],
                        self.kiwoom.watch[condition_name][code]['buy_time'],
                        self.kiwoom.watch[condition_name][code]['high'],
                        self.kiwoom.watch[condition_name][code]['high_price_rate'],
                        self.kiwoom.watch[condition_name][code]['high_volume'],
                        self.kiwoom.watch[condition_name][code]['high_volume_rate'],
                        self.kiwoom.watch[condition_name][code]['high_trade_power'],
                        self.kiwoom.watch[condition_name][code]['sell'],
                        self.kiwoom.watch[condition_name][code]['sell_price_rate'],
                        self.kiwoom.watch[condition_name][code]['sell_volume'],
                        self.kiwoom.watch[condition_name][code]['sell_volume_rate'],
                        self.kiwoom.watch[condition_name][code]['sell_trade_power'],
                        self.kiwoom.watch[condition_name][code]['sell_time'],
                        self.kiwoom.watch[condition_name][code]['earning_rate']) + "\n"
                        """


                        # 2020.03.21 (토) 수정
                        if self.kiwoom.watch[condition_name][code]['first_partial_sell_stock_number'] != 0:

                            tracker = True      # 2020.07.08 (수) 추가

                            self.kiwoom.watch[condition_name][code]['order_status'] = '매도 시작'  # 2019.10.16 (수) 추가
                            # self.kiwoom.watch[condition_name][code]['order_status'] = self.kiwoom.watch[condition_name][code]['order_status_1']  # 2019.10.16 (수) 추가


                            # 2020.06.23 (화) 추가
                            current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']

                            order_time_interval = (current - self.kiwoom.check['time']['last_send_order_time']).total_seconds()       # 2020.06.23 (화) 수정 - .seconds 에서 .total_seconds() 로 수정       # 2020.06.24 (수) 수정
                            if self.send_order_time_interval > order_time_interval:
                                sleep_time = self.send_order_time_interval - order_time_interval
                                time.sleep(sleep_time)

                            self.send_sell(code, self.kiwoom.watch[condition_name][code]['first_partial_sell_stock_number'], int(self.kiwoom.watch[condition_name][code]['current'] * self.sell_damper_2), self.sell_type, condition_name)       # 2019.11.13 (수) 수정 - 시장가 비슷하게 빠르게 매도      # 2019.11.29 (금) 수정     # 2020.06.08 (월) 수정 - condition_name 추가

                            # 2020.06.23 (화) 추가
                            self.kiwoom.check['time']['last_send_order_time'] = current     # 2020.06.24 (수) 수정


                        else:       # 2020.03.24 (화) 추가 - For Test Mode
                            self.kiwoom.watch[condition_name][code]['total_sell_price'] += self.kiwoom.watch[condition_name][code]['current'] * 1       # 2022.10.09 (일) 수정
                            # self.kiwoom.watch[condition_name][code]['trade_total_sell_price'] = self.kiwoom.watch[condition_name][code]['current'] * 1        # 2022.10.09 (일) 수정
                            self.kiwoom.watch[condition_name][code]['total_buy_price'] += self.kiwoom.watch[condition_name][code]['buy'] * 1


                        # Sell Stage, 수익률, 매도가, 매수가 표시 그 다음 수익금 출력

                        # 2020.08.04 (화) 추가
                        if self.kiwoom.watch[condition_name][code]['survey_check'] == True:
                            self.kiwoom.watch[condition_name]['condition_survey_profit'] -= self.kiwoom.watch[condition_name][code]['profit']
                            self.kiwoom.watch['total_survey_profit'] -= self.kiwoom.watch[condition_name][code]['profit']

                        # 2020.02.29 (토) 추가
                        self.kiwoom.watch[condition_name]['condition_profit'] -= self.kiwoom.watch[condition_name][code]['profit']
                        self.kiwoom.watch['total_profit'] -= self.kiwoom.watch[condition_name][code]['profit']
                        # 2019.08.06 (화) 추가 - 수익금 표시 함수 추가      # 2020.02.29 (토) 수정
                        self.kiwoom.watch[condition_name][code]['first_partial_profit'] = int(self.kiwoom.watch[condition_name][code]['current'] * self.kiwoom.watch[condition_name][code]['first_partial_sell_stock_number'] * (1 - (self.commission_rate / 100) - (self.tax_rate / 100))) - int(self.kiwoom.watch[condition_name][code]['buy'] * self.kiwoom.watch[condition_name][code]['first_partial_sell_stock_number'] * (1 + (self.tax_rate / 100)))
                        self.kiwoom.watch[condition_name][code]['profit'] = self.kiwoom.watch[condition_name][code]['first_partial_profit']
                        self.kiwoom.watch[condition_name][code]['profit'] += int(self.kiwoom.watch[condition_name][code]['current'] * self.kiwoom.watch[condition_name][code]['left_stock_number'] * (1 - (self.commission_rate / 100) - (self.tax_rate / 100))) - int(self.kiwoom.watch[condition_name][code]['buy'] * self.kiwoom.watch[condition_name][code]['left_stock_number'] * (1 + (self.tax_rate / 100)))
                        # 2020.02.29 (토) 추가
                        self.kiwoom.watch[condition_name]['condition_profit'] += self.kiwoom.watch[condition_name][code]['profit']
                        self.kiwoom.watch['total_profit'] += self.kiwoom.watch[condition_name][code]['profit']

                        # 2020.08.04 (화) 추가
                        if self.kiwoom.watch[condition_name][code]['survey_check'] == True:
                            self.kiwoom.watch[condition_name]['condition_survey_profit'] += self.kiwoom.watch[condition_name][code]['profit']
                            self.kiwoom.watch['total_survey_profit'] += self.kiwoom.watch[condition_name][code]['profit']

                        # 2020.02.29 (일) 수정
                        # # Temp Code
                        # if not self.kiwoom.watch[condition_name]['condition_profit']:
                        #     self.kiwoom.watch[condition_name]['condition_profit'] = 0

                        # self.kiwoom.watch[condition_name]['condition_profit'] += self.kiwoom.watch[condition_name][code]['profit']        # 2020.02.26 (수) 수정

                        # 2020.02.29 (토) 수정
                        # if not self.kiwoom.watch['total_profit']:
                        #     self.kiwoom.watch['total_profit'] = 0

                        # self.kiwoom.watch['total_profit'] += self.kiwoom.watch[condition_name][code]['profit']        # 2020.02.26 (수) 수정


                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_7_1_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_7_1_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_7_1_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_7_1_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 7-1 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 7-1 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 7-1 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)
                            self.logTextEdit_2.append(text)
                            text = text.replace(", ", "\n")
                            self.kiwoom.send_telegram_message(chat_id=self.kiwoom.info['telegram_id'], text=text)  # 2019.12.04 (수) 수정

                        text = 'Code Profit: [%s] %s' % (self.check_profit(self.kiwoom.watch[condition_name][code]['profit']), "{:,}".format(self.kiwoom.watch[condition_name][code]['profit']))        # 2020.06.25 (목) 수정
                        # text = 'Code Profit: %s' % ("{:,}".format(self.kiwoom.watch[condition_name][code]['profit']))       # 2020.05.16 (토) 수정 - 1,000 단위 콤마 추가      # 2020.06.25 (목) 수정
                        self.kiwoom.print_log(text=text)
                        self.logTextEdit_2.append(text)
                        text = 'Condition Profit: [%s] %s' % (self.check_profit(self.kiwoom.watch[condition_name]['condition_profit']), "{:,}".format(self.kiwoom.watch[condition_name]['condition_profit']))       # 2020.06.25 (목) 수정
                        # text = 'Condition Profit: %s' % ("{:,}".format(self.kiwoom.watch[condition_name]['condition_profit']))      # 2020.05.16 (토) 수정 - 1,000 단위 콤마 추가      # 2020.06.25 (목) 수정
                        self.kiwoom.print_log(text=text)
                        self.logTextEdit_2.append(text)
                        text = 'Total Profit: [%s] %s' % (self.check_profit(self.kiwoom.watch['total_profit']), "{:,}".format(self.kiwoom.watch['total_profit']))       # 2020.06.25 (목) 수정
                        # text = 'Total Profit: %s' % ("{:,}".format(self.kiwoom.watch['total_profit']))      # 2020.05.16 (토) 수정 - 1,000 단위 콤마 추가      # 2020.06.25 (목) 수정
                        self.kiwoom.print_log(text=text)
                        self.logTextEdit_2.append(text)

                        self.kiwoom.watch[condition_name][code]['first_partial_sell_end'] = True

                        text = 'self.kiwoom.watch[condition_name][code][first_partial_sell_end]: %s' % (self.kiwoom.watch[condition_name][code]['first_partial_sell_end'])
                        self.kiwoom.print_log(text=text)


                    # Temp Name
                    elif self.partial_sell == True and self.second_partial_sell == True and self.kiwoom.watch[condition_name][code]['second_partial_sell_end'] == False and self.kiwoom.watch[condition_name][code]['earning_rate'] >= self.second_partial_sell_target_percent:     # 2020.06.22 (월) 수정
                    # if self.partial_sell == True and self.second_partial_sell == True and self.kiwoom.watch[condition_name][code]['second_partial_sell_end'] == False and self.kiwoom.watch[condition_name][code]['earning_rate'] >= self.second_partial_sell_target_percent:       # 2020.05.21 (목) 수정       # 2020.06.22 (월) 수정
                    # elif self.partial_sell == True and self.second_partial_sell == True and self.kiwoom.watch[condition_name][code]['second_partial_sell_end'] == False and self.kiwoom.watch[condition_name][code]['earning_rate'] >= self.second_partial_sell_target_percent:      # 2019.08.03 (토) 추가      # 2020.05.21 (목) 수정

                        self.kiwoom.watch[condition_name][code]['second_partial_sell_stock_number'] = int(self.kiwoom.watch[condition_name][code]['left_stock_number'] * (self.second_partial_sell_ratio / (1 - self.first_partial_sell_ratio)))

                        self.kiwoom.watch[condition_name][code]['left_stock_number'] = self.kiwoom.watch[condition_name][code]['left_stock_number'] - self.kiwoom.watch[condition_name][code]['second_partial_sell_stock_number']

                        # 2020.03.21 (토) 수정
                        if self.kiwoom.watch[condition_name][code]['second_partial_sell_stock_number'] != 0:

                            tracker = True      # 2020.07.08 (수) 추가

                            self.kiwoom.watch[condition_name][code]['order_status'] = '매도 시작'       # 2019.10.16 (수) 추가
                            # self.kiwoom.watch[condition_name][code]['order_status'] = self.kiwoom.watch[condition_name][code]['order_status_1']       # 2019.10.16 (수) 추가


                            # 2020.06.23 (화) 추가
                            current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']

                            order_time_interval = (current - self.kiwoom.check['time']['last_send_order_time']).total_seconds()       # 2020.06.23 (화) 수정 - .seconds 에서 .total_seconds() 로 수정       # 2020.06.24 (수) 수정
                            if self.send_order_time_interval > order_time_interval:
                                sleep_time = self.send_order_time_interval - order_time_interval
                                time.sleep(sleep_time)

                            self.send_sell(code, self.kiwoom.watch[condition_name][code]['second_partial_sell_stock_number'], int(self.kiwoom.watch[condition_name][code]['current'] * self.sell_damper_2), self.sell_type, condition_name)      # 2019.11.13 (수) 수정 - 시장가 비슷하게 빠르게 매도      # 2019.11.29 (금) 수정     # 2020.06.08 (월) 수정 - condition_name 추가

                            # 2020.06.23 (화) 추가
                            self.kiwoom.check['time']['last_send_order_time'] = current     # 2020.06.24 (수) 수정


                        else:   # 2020.03.24 (화) 추가 - For Test Mode
                            self.kiwoom.watch[condition_name][code]['total_sell_price'] += self.kiwoom.watch[condition_name][code]['current'] * 1       # 2022.10.09 (일) 수정
                            # self.kiwoom.watch[condition_name][code]['trade_total_sell_price'] += self.kiwoom.watch[condition_name][code]['current'] * 1       # 2022.10.09 (일) 수정
                            self.kiwoom.watch[condition_name][code]['total_buy_price'] += self.kiwoom.watch[condition_name][code]['buy'] * 1

                        # 2020.08.04 (화) 추가
                        if self.kiwoom.watch[condition_name][code]['survey_check'] == True:
                            self.kiwoom.watch[condition_name]['condition_survey_profit'] -= self.kiwoom.watch[condition_name][code]['profit']
                            self.kiwoom.watch['total_survey_profit'] -= self.kiwoom.watch[condition_name][code]['profit']

                        # 2020.02.29 (토) 추가
                        self.kiwoom.watch[condition_name]['condition_profit'] -= self.kiwoom.watch[condition_name][code]['profit']
                        self.kiwoom.watch['total_profit'] -= self.kiwoom.watch[condition_name][code]['profit']
                        # 2019.08.06 (화) 추가 - 수익금 표시 함수 추가      # 2020.02.29 (토) 수정
                        self.kiwoom.watch[condition_name][code]['second_partial_profit'] = int(self.kiwoom.watch[condition_name][code]['current'] * self.kiwoom.watch[condition_name][code]['second_partial_sell_stock_number'] * (1 - (self.commission_rate / 100) - (self.tax_rate / 100))) - int(self.kiwoom.watch[condition_name][code]['buy'] * self.kiwoom.watch[condition_name][code]['second_partial_sell_stock_number'] * (1 + (self.tax_rate / 100)))
                        self.kiwoom.watch[condition_name][code]['profit'] = self.kiwoom.watch[condition_name][code]['second_partial_profit']
                        self.kiwoom.watch[condition_name][code]['profit'] += self.kiwoom.watch[condition_name][code]['first_partial_profit']
                        self.kiwoom.watch[condition_name][code]['profit'] += int(self.kiwoom.watch[condition_name][code]['current'] * self.kiwoom.watch[condition_name][code]['left_stock_number'] * (1 - (self.commission_rate / 100) - (self.tax_rate / 100))) - int(self.kiwoom.watch[condition_name][code]['buy'] * self.kiwoom.watch[condition_name][code]['left_stock_number'] * (1 + (self.tax_rate / 100)))
                        # 2020.02.29 (토) 추가
                        self.kiwoom.watch[condition_name]['condition_profit'] += self.kiwoom.watch[condition_name][code]['profit']
                        self.kiwoom.watch['total_profit'] += self.kiwoom.watch[condition_name][code]['profit']

                        # 2020.08.04 (화) 추가
                        if self.kiwoom.watch[condition_name][code]['survey_check'] == True:
                            self.kiwoom.watch[condition_name]['condition_survey_profit'] += self.kiwoom.watch[condition_name][code]['profit']
                            self.kiwoom.watch['total_survey_profit'] += self.kiwoom.watch[condition_name][code]['profit']

                        # Temp Code
                        # if not self.kiwoom.watch[condition_name]['condition_profit']:
                        #     self.kiwoom.watch[condition_name]['condition_profit'] = 0

                        # self.kiwoom.watch[condition_name]['condition_profit'] += self.kiwoom.watch[condition_name][code]['profit']        # 2020.02.26 (수) 수정

                        # if not self.kiwoom.watch['total_profit']:
                        #     self.kiwoom.watch['total_profit'] = 0

                        # self.kiwoom.watch['total_profit'] += self.kiwoom.watch[condition_name][code]['profit']        # 2020.02.26 (수) 수정


                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_7_2_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_7_2_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_7_2_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_7_2_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 7-2 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 7-2 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 7-2 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)
                            self.logTextEdit_2.append(text)
                            text = text.replace(", ", "\n")
                            self.kiwoom.send_telegram_message(chat_id=self.kiwoom.info['telegram_id'], text=text)  # 2019.12.04 (수) 수정

                        text = 'Code Profit: [%s] %s' % (self.check_profit(self.kiwoom.watch[condition_name][code]['profit']), "{:,}".format(self.kiwoom.watch[condition_name][code]['profit']))        # 2020.06.25 (목) 수정
                        # text = 'Code Profit: %s' % ("{:,}".format(self.kiwoom.watch[condition_name][code]['profit']))       # 2020.05.16 (토) 수정 - 1,000 단위 콤마 추가      # 2020.06.25 (목) 수정
                        self.kiwoom.print_log(text=text)
                        self.logTextEdit_2.append(text)
                        text = 'Condition Profit: [%s] %s' % (self.check_profit(self.kiwoom.watch[condition_name]['condition_profit']), "{:,}".format(self.kiwoom.watch[condition_name]['condition_profit']))       # 2020.06.25 (목) 수정
                        # text = 'Condition Profit: %s' % ("{:,}".format(self.kiwoom.watch[condition_name]['condition_profit']))      # 2020.05.16 (토) 수정 - 1,000 단위 콤마 추가      # 2020.06.25 (목) 수정
                        self.kiwoom.print_log(text=text)
                        self.logTextEdit_2.append(text)
                        text = 'Total Profit: [%s] %s' % (self.check_profit(self.kiwoom.watch['total_profit']), "{:,}".format(self.kiwoom.watch['total_profit']))       # 2020.06.25 (목) 수정
                        # text = 'Total Profit: %s' % ("{:,}".format(self.kiwoom.watch['total_profit']))      # 2020.05.16 (토) 수정 - 1,000 단위 콤마 추가      # 2020.06.25 (목) 수정
                        self.kiwoom.print_log(text=text)
                        self.logTextEdit_2.append(text)

                        self.kiwoom.watch[condition_name][code]['second_partial_sell_end'] = True

                        text = 'self.kiwoom.watch[condition_name][code][second_partial_sell_end]: %s' % (self.kiwoom.watch[condition_name][code]['second_partial_sell_end'])
                        self.kiwoom.print_log(text=text)




                    #self.keeping_time_second_for_partial_sell





                    # 매도시점 8 [ Sell Stage 8 ] - 보유 시간 도달 매도, TBD        # 2019.09.28 (토) 추가
                    current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']      # 2020.02.23 (일) 추가
                    self.kiwoom.watch[condition_name][code]['current_time'] = current       # 2020.02.23 (일) 수정
                    self.kiwoom.watch[condition_name][code]['keeping_time'] = (self.kiwoom.watch[condition_name][code]['current_time'] - self.kiwoom.watch[condition_name][code]['buy_end_time_2']).total_seconds()     # 2020.04.12 (일) 수정     # 2020.06.23 (화) 수정 - .seconds 에서 .total_seconds() 로 수정
                    # self.kiwoom.watch[condition_name][code]['keeping_time'] = (self.kiwoom.watch[condition_name][code]['current_time'] - self.kiwoom.watch[condition_name][code]['buy_time_2']).seconds       # 2020.04.12 (일) 수정

                    if self.time_limitation == True and self.kiwoom.watch[condition_name][code]['keeping_time'] >= self.keeping_time_second:
                        status = 3

                        tracker = True      # 2020.07.08 (수) 추가

                        # 2020.07.06 (월) 추가 및 수정
                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_8_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_8_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_8_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_8_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 8 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 8 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 8 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)



                    # 매도시점 10 [ Sell Stage 10 ] - 상한가 도달 시 매도       # 2021.01.15 (금) 추가
                    if ((self.kiwoom.watch[condition_name][code]['current'] - self.kiwoom.watch[condition_name][code]['before_price']) / self.kiwoom.watch[condition_name][code]['before_price']) * 100 > 29.0:
                        status = 3

                        tracker = True

                        current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                        # current_time = current.time()

                        check_time = str(current.hour) + str(current.minute)

                        if not self.kiwoom.watch[condition_name][code]['sell_stage_10_check_time_list']:
                            self.kiwoom.watch[condition_name][code]['sell_stage_10_check_time_list'] = []

                        if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_10_check_time_list']).intersection(set([check_time]))) == 0:
                            self.kiwoom.watch[condition_name][code]['sell_stage_10_check_time_list'].append(check_time)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 10 ]'
                            else:
                                self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 10 ]'

                            text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 10 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                            self.kiwoom.print_log(text=text)



                    # 매도시점 11 [ Sell Stage 11 ] - 전체 수익금 목표 수익금 2배(Factor) 도달      # 2020.02.29 (토) 추가
                    if self.profit_check == True:
                        if self.kiwoom.watch[condition_name]['profit_check'] == "수익 종료 1":
                            status = 3

                            tracker = True      # 2020.07.08 (수) 추가

                            # 2020.07.06 (월) 추가 및 수정
                            current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                            # current_time = current.time()

                            check_time = str(current.hour) + str(current.minute)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage_11_check_time_list']:
                                self.kiwoom.watch[condition_name][code]['sell_stage_11_check_time_list'] = []

                            if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_11_check_time_list']).intersection(set([check_time]))) == 0:
                                self.kiwoom.watch[condition_name][code]['sell_stage_11_check_time_list'].append(check_time)

                                if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 11 ]'
                                else:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 11 ]'

                                text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 11 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                                self.kiwoom.print_log(text=text)


                    # 매도시점 12 [ Sell Stage 12 ] - 전체 수익금 목표 수익금 도달 후 일 정 Factor 하락      # 2020.02.29 (토) 추가
                    if self.profit_check == True:
                        if self.kiwoom.watch[condition_name]['profit_check'] == "수익 종료 2":
                            status = 3

                            tracker = True      # 2020.07.08 (수) 추가

                            # 2020.07.06 (월) 추가 및 수정
                            current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                            # current_time = current.time()

                            check_time = str(current.hour) + str(current.minute)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage_12_check_time_list']:
                                self.kiwoom.watch[condition_name][code]['sell_stage_12_check_time_list'] = []

                            if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_12_check_time_list']).intersection(set([check_time]))) == 0:
                                self.kiwoom.watch[condition_name][code]['sell_stage_12_check_time_list'].append(check_time)

                                if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 12 ]'
                                else:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 12 ]'

                                text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 12 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                                self.kiwoom.print_log(text=text)


                    # 매도시점 13 [ Sell Stage 13 ] - 전체 손실금 손절 손실금 도달      # 2020.02.29 (토) 추가
                    if self.profit_check == True:
                        if self.kiwoom.watch[condition_name]['profit_check'] == "손실 종료":
                            status = 3

                            tracker = True      # 2020.07.08 (수) 추가

                            # 2020.07.06 (월) 추가 및 수정
                            current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                            # current_time = current.time()

                            check_time = str(current.hour) + str(current.minute)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage_13_check_time_list']:
                                self.kiwoom.watch[condition_name][code]['sell_stage_13_check_time_list'] = []

                            if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_13_check_time_list']).intersection(set([check_time]))) == 0:
                                self.kiwoom.watch[condition_name][code]['sell_stage_13_check_time_list'].append(check_time)

                                if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 13 ]'
                                else:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 13 ]'

                                text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 13 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                                self.kiwoom.print_log(text=text)


                    # 매도시점 21 [ Sell Stage 21 ] - 목표 수익 종목 수 도달      # 2020.02.29 (토) 추가
                    if self.win_lose_check == True:
                        if not self.kiwoom.watch[condition_name]['win_lose_check']:
                            pass
                        elif self.kiwoom.watch[condition_name]['win_lose_check'] == "수익 종료":
                            status = 3

                            tracker = True      # 2020.07.08 (수) 추가

                            # 2020.07.06 (월) 추가 및 수정
                            current = datetime.datetime.now() - self.kiwoom.check['time']['current_delta']
                            # current_time = current.time()

                            check_time = str(current.hour) + str(current.minute)

                            if not self.kiwoom.watch[condition_name][code]['sell_stage_21_check_time_list']:
                                self.kiwoom.watch[condition_name][code]['sell_stage_21_check_time_list'] = []

                            if len(set(self.kiwoom.watch[condition_name][code]['sell_stage_21_check_time_list']).intersection(set([check_time]))) == 0:
                                self.kiwoom.watch[condition_name][code]['sell_stage_21_check_time_list'].append(check_time)

                                if not self.kiwoom.watch[condition_name][code]['sell_stage']:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = '[ Sell Stage 21 ]'
                                else:
                                    self.kiwoom.watch[condition_name][code]['sell_stage'] = self.kiwoom.watch[condition_name][code]['sell_stage'] + ' and ' + '[ Sell Stage 21 ]'

                                text = 'Condition Name: %s, Code: %s, 종목명: %s - [ Sell Stage 21 ]' % (condition_name, code, self.kiwoom.watch[condition_name][code]['stock_name'])
                                self.kiwoom.print_log(text=text)
