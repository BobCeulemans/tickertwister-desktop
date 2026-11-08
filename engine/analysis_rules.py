"""Original analysis rules by Bob Ceulemans, MD (2022), Apache-2.0.
Migrated from Tickertwister: isolated state, fiscal dates, validated data access.
See docs/ANALYSIS.md for migration conventions. Do not instantiate directly.
"""
from datetime import datetime, date
import math
import pandas as pd
from markupsafe import Markup

def strict_divide(a, b):
    if not math.isfinite(float(a)) or not math.isfinite(float(b)) or b == 0:
        raise ValueError('Missing value or zero denominator')
    return a / b

class Score:
    """ Default Values Weights (w) - Set weights according your preference of importance! """
    w_APTR = 2
    w_ARRev = 6
    w_ARRev_decreasing = 2
    w_ARRev_increasing = 2
    w_ARTR = 2
    w_bb = 9
    w_CapexNI = 2
    w_CapexNI_decreasing = 2
    w_CapexNI_increasing = 1
    w_CapexNI_y0_negative = 2
    w_Cash = 1
    w_Cash_decreasing = 0.5
    w_Cash_increasing = 0.5
    w_CCC = 2
    w_CCC_all_negative = 4
    w_CR = 6
    w_CR_decreasing = 2
    w_CR_increasing = 2
    w_DE = 9
    w_DE_decreasing = 3
    w_DE_increasing = 3
    w_DepGP = 2
    w_DepGP_decreasing = 1
    w_DepGP_increasing = 1
    w_DIOH = 2
    w_dividends = 6
    w_dividends_decreasing = 2
    w_dividends_increasing = 2
    w_DPO = 2
    w_DRO = 2
    w_EPS = 4
    w_EVEBITDA = 0.5
    w_FCF = 9
    w_FCF_decreasing = 3
    w_FCF_growth_2000bp = 3
    w_FCF_increasing = 3
    w_FCFE = 4
    w_FCFE_decreasing = 3
    w_FCFE_growth_2000bp = 2
    w_FCFE_increasing = 2
    w_FCFF = 4
    w_FCFF_decreasing = 3
    w_FCFF_growth_2000bp = 2
    w_FCFF_increasing = 2
    w_forwardPE = 0.5
    w_forwardPEG = 0.5
    w_GPM = 4
    w_GPM_decreasing = 2
    w_GPM_increasing = 2
    w_IEOP = 2
    w_IEOP_decreasing = 1
    w_IEOP_increasing = 1
    w_Inv_NItC = 4
    w_ITR = 2
    w_netBorM_decreasing = 2
    w_netBorM_increasing = 2
    w_NPM = 4
    w_NPM_decreasing = 2
    w_NPM_increasing = 2
    w_PB = 0.5
    w_QR = 2
    w_QR_decreasing = 1
    w_QR_increasing = 1
    w_RaD = 2
    w_RaD_decreasing = 1
    w_RaD_increasing = 1
    w_RE = 9
    w_ROA = 9
    w_ROA_decreasing = 3
    w_ROA_increasing = 3
    w_RONTA = 9
    w_RONTA_increasing = 3
    w_RONTA_decreasing = 3
    w_ROE = 9
    w_ROE_decreasing = 3
    w_ROE_increasing = 3
    w_SGA = 2
    w_SGA_decreasing = 1
    w_SGA_increasing = 1
    w_TLE = 3
    w_TLE_decreasing = 1.5
    w_TLE_increasing = 1.5
    w_trailingPE = 0.5
    w_trailingPEG = 0.5
    ' Points factor (pf) - Preferably Do NOT change these values! '
    pf_neg = 0
    pf_mod = 0.5
    pf_pos = 1

class Dictionary:
    """ Dictionary """
    address1 = (11, 'Address1', 'Addr.')
    ask = (137, 'Ask Stock Price', 'Price.ASK')
    askSize = (138, 'Ask Size', 'ASK.Sz.')
    averageDailyVolume10Day = (112, 'Daily Avg. Volume Shares Trading (10d)', 'Daily.Avg.Shares.Volume (10d)')
    averageDailyVolume10DayToFloat = (112.2, 'Daily Avg. Volume/Float(10d)', 'Daily.Avg.Volume/Float (10d)')
    averageDailyVolume10DayToSO = (112.1, 'Daily Avg. Volume/Share Outstanding (10d)', 'Daily.Avg.Volume/SO (10d)')
    averageVolume = (135, 'Avg. Volume Shares Trading', 'Avg.Shares.Volume')
    beta = (83, 'Beta (β)', 'β')
    bid = (144, 'Bid Stock Price', 'Price.BID')
    bidSize = (147, 'Bid Size', 'BID.Sz.')
    bookValue = (65, 'Bookvalue (ps)', 'BV.PS')
    city = (4, 'City', 'CTY')
    country = (7, 'Country', 'Ctry.')
    currency = (126, 'Currency', 'Curr.')
    currentPrice = (25, 'Current Stock Price', 'Price')
    currentRatio = (27, 'Current Ratio', 'CR')
    dayHigh = (148, 'Day High Stock Price', 'Price.DayHigh')
    dayLow = (136, 'Day Low Stock Price', 'Price.DayLow')
    debtToEquity = (31, 'Debt to Equity (D/E)', 'D/E')
    dividendRate = (121, 'Forward Annual Dividend Rate (ps)', 'Div.R. (Fwd)')
    dividendYield = (146, 'Forward Annual Dividend Yield', 'Div.Yld (Fwd)')
    earningsGrowth = (26, 'Growth Earnings', 'E.G')
    earningsQuarterlyGrowth = (92, 'Growth Earnings (Q)', 'E.qG)')
    ebitda = (19, 'EBITDA', 'EBITDA')
    ebitdaMargins = (13, 'EBITDA Margin', 'EBITDA.M')
    enterpriseToEbitda = (56, 'Enterprise value to EBITDA', 'EV/EBITDA')
    enterpriseToRevenue = (54, 'Enterprise value to Sales', 'EV/Sales')
    enterpriseValue = (84, 'Enterprise value', 'EV')
    exchange = (42, 'Exchange', 'Exch.')
    exchangeTimezoneName = (45, 'Timezone Exchange', 'TMZ.Exch.')
    exchangeTimezoneShortName = (46, 'Timezone Exchange (short)', 'S.TMZ.Exch.')
    exDividendDate = (122, 'Ex Dividend Date', 'Div.Dt.Ex')
    fiftyDayAverage = (114, '50d Avg. Stock Price', 'Price.Avg.50d')
    fiftyTwoWeekHigh = (140, '52w High Stock Price', 'Price.High.52w')
    fiftyTwoWeekLow = (143, '52w Low Stock Price', 'Price.Low.52w')
    fiveYearAvgDividendYield = (142, '5y Avg. Annual Dividend Yield', 'Avg.Div.Yld.5y')
    floatShares = (82, 'Float Shares Outstanding', 'Shares.Float')
    forwardEps = (59, 'Forward EPS', 'EPS (Fwd)')
    forwardPE = (97, 'Forward P/E', 'P/E (Fwd)')
    freeCashflow = (23, 'Levered Free Cashflow (FCFE)', 'FCFE')
    fullTimeEmployees = (2, 'Full Time Employees', 'Empl.')
    grossMargins = (15, 'Gross Margin', 'GM')
    grossProfits = (22, 'Gross Profits', 'GP')
    heldPercentIndividuals = (70.1, 'Shares Held by Individuals (%)', 'Shares.Individuals')
    heldPercentInsiders = (76, 'Shares Held by Insiders (%)', 'Shares.Insiders')
    heldPercentInstitutions = (70, 'Shares Held by Institutions (%)', 'Shares.Institutions')
    industry = (12, 'Industry', 'Ind.')
    lastDividendValue = (73, 'Last Dividend (ps)', 'Div.PS (last)')
    lastSplitFactor = (88, 'Last Split Factor Share Outstanding', 'Shares.Last.Split')
    logo_url = (151, 'Logo URL', 'URL.Logo')
    longBusinessSummary = (3, 'Business Summary', 'Summ.')
    longName = (44, 'Name', 'N')
    market = (52, 'Market', 'M')
    marketCap = (132, 'Market capitalization', 'MCap.')
    messageBoardId = (51, 'Message Board ID', 'Mess.B.ID')
    netIncomeToCommon = (71, 'Net Income To Common', 'NITCS')
    numberOfAnalystOpinions = (29, 'Analyst Opinions (N°)', 'Analyst.Opinions')
    openInterest = (131, 'Options Trading Open Interest', 'Options.Open.Interest')
    operatingCashflow = (16, 'Operating Cashflow', 'Op.CF')
    operatingMargins = (18, 'Operating Margin', 'OM')
    payoutRatio = (108, 'Payout Ratio', 'PO')
    pegRatio = (95, 'Forward PEG', 'PEG (Fwd)')
    phone = (5, 'Phone', 'Ph.')
    previousClose = (104, 'Previous Close Stock Price', 'Price.Close.Prev')
    priceOpen = (116, 'Open Stock Price', 'Price.Open')
    priceToBook = (75, 'Price to Bookvalue', 'P/B')
    priceToSalesTrailing12Months = (93, 'Trailing Price to Sales', 'P/Sales (ttm)')
    profitMargins = (14, 'Profit Margin', 'PM')
    quickRatio = (40, 'Quick Ratio', 'QR')
    quoteType = (49, 'Quote Type', 'QT')
    recommendationKey = (21, 'Analyst Recommendation', 'Analyst.Recomm.')
    recommendationMean = (41, 'Analyst Recommendation (mean)', 'Analyst.Recomm. (mean)')
    returnOnAssets = (28, 'Return on Assets', 'ROA')
    returnOnEquity = (32, 'Return on Equity', 'ROE')
    revenueGrowth = (17, 'Growth Sales', 'Sales.G')
    revenuePerShare = (39, 'Total Revenue (ps)', 'TS.PS')
    revenueQuarterlyGrowth = (60, 'Growth Sales (Q)', 'Sales (qG)')
    sector = (1, 'Sector(s)', 'Sect.')
    sharesOutstanding = (61, 'Shares Outstanding', 'SO')
    sharesShort = (66, 'Short Shares Outstanding', 'Short.SO')
    sharesShortPriorMonth = (100, 'Short Shares Outstanding Prior Month', 'Short.SO.Prior.Month')
    shortPercentOfFloat = (99, 'Short (%) of Float', 'Short.Float')
    shortRatio = (80, 'Short Ratio', 'Short.Ratio')
    state = (6, 'State', 'St.')
    strikePrice = (134, 'Options Trading Strike Price', 'Options.Price.Strike')
    symbol = (50, 'Ticker', 'T.')
    targetHighPrice = (33, 'Analyst Target Price High', 'Price.Target.High')
    targetLowPrice = (20, 'Analyst Target Price Low', 'Price.Target.Low')
    targetMeanPrice = (30, 'Analyst Target Price Mean', 'Price.Target.Mean')
    targetMedianPrice = (24, 'Analyst Target Price Median', 'Price.Target.Median')
    totalCash = (34, 'Total Cash', 'Tot.Cash')
    totalCashPerShare = (37, 'Total Cash (ps)', 'Tot.Cash.PS')
    totalDebt = (35, 'Total Debt', 'TD')
    totalRevenue = (36, 'Total Revenue', 'TS')
    tradeable = (145, 'Options Treadable', 'Tradable')
    trailingAnnualDividendRate = (115, 'Trailing Annual Dividend Rate (ps)', 'Div.R (ttm)')
    trailingAnnualDividendYield = (107, 'Trailing Annual Dividend Yield', 'Div.Yld (ttm)')
    trailingEps = (72, 'Trailing EPS', 'EPS (ttm)')
    trailingPE = (127, 'Trailing P/E', 'P/E (ttm)')
    trailingPegRatio = (152, 'Trailing PEG', 'PEG (ttm)')
    twoHundredDayAverage = (106, '200d Avg. Stock Price', 'Price.Avg.200d')
    volume = (139, 'Volume Shares Trading', 'Shares.Volume')
    website = (9, 'Website', 'www')
    zipcode = (0, 'Zipcode', 'ZIP')

class OriginalAnalysisRules:

    def longName(self):
        """ Long Company Name """
        data = self.data
        try:
            longName = data['longName']
            return longName
        except:
            return Markup("❓ <span class='text-info'>No data about Business Name!")

    def address(self):
        """ Address """
        data = self.data
        try:
            address = data['address1']
            return address
        except KeyError:
            address = ''
            return address

    def city(self):
        """ City """
        data = self.data
        try:
            city = data['city']
            return city
        except KeyError:
            city = ''
            return city

    def state(self):
        """ State """
        data = self.data
        try:
            state = data['state']
            return state
        except KeyError:
            state = ''
            return state

    def zipcode(self):
        """ Zipcode """
        data = self.data
        try:
            zipcode = data['zip']
            return zipcode
        except KeyError:
            zipcode = ''
            return zipcode

    def country(self):
        """ Country """
        data = self.data
        try:
            country = data['country']
            return country
        except KeyError:
            country = ''
            return country

    def phone(self):
        """ Phone """
        data = self.data
        try:
            return Markup('✆ ' + data['phone'])
        except KeyError:
            phone = ''
            return phone

    def website(self):
        """ Website """
        data = self.data
        try:
            return Markup("<a href='" + str(data['website']) + "'>" + str(data['website']) + '</a>')
        except KeyError:
            website = ''
            return website

    def logoUrl(self):
        """ URL Company's Logo """
        data = self.data
        try:
            logoUrl = data['logo_url']
            return logoUrl
        except KeyError:
            logoUrl = ''
            return logoUrl

    def businessSector(self):
        """ Business sector """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.sector[1] + ': ' + str(data['sector']))
        except KeyError:
            sector = ''
            return sector

    def businessIndustry(self):
        """ Business industry """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.industry[1] + ': ' + str(data['industry']))
        except KeyError:
            industry = ''
            return industry

    def fullTimeEmployees(self):
        """ Fulltime employees """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.fullTimeEmployees[1] + ': ' + str('{:,}'.format(data['fullTimeEmployees'])))
        except KeyError:
            fullTimeEmployees = ''
            return fullTimeEmployees

    def businessSummary(self):
        """ Business Summary """
        data = self.data
        try:
            summary = str(data['longBusinessSummary'])
            return summary
        except KeyError:
            summary = ''
            return summary

    def symbol(self):
        """ Symbol """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.symbol[1] + ': ' + str(data['symbol']))
        except:
            return Markup("❓ <span class='text-info'>No data about Symbol/Ticker!")

    def market(self):
        """ Market """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.market[1] + ': ' + str(data['market']))
        except:
            return Markup("❓ <span class='text-info'>No data about Market!")

    def exchangeTimezoneName(self):
        """ Exchange Timezone Name """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.exchangeTimezoneName[1] + ': ' + str(data['exchangeTimezoneName']) + ' (' + str(data['exchangeTimezoneShortName']) + ')')
        except:
            return Markup("❓ <span class='text-info'>No data about Exchange Timezone Name!")

    def exchange(self):
        """ Exchange """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.exchange[1] + ': ' + str(data['exchange']))
        except:
            return Markup("❓ <span class='text-info'>No data about Exchange!")

    def quoteType(self):
        """ Quote Type """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.quoteType[1] + ': ' + str(data['quoteType']))
        except:
            return Markup("❓ <span class='text-info'>No data about Quote Type!")

    def messageBoardId(self):
        """ Message Board Id """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.messageBoardId[1] + ': ' + str(data['messageBoardId']))
        except:
            return Markup("❓ <span class='text-info'>No data about Message Board Id!")

    def currency(self):
        """ Currency """
        data = self.data
        try:
            self.fundamentals['currency'] = data['currency']
            currency = data['currency']
            return currency
        except:
            pass

    def currencyText(self):
        """ Currency """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.currency[1] + ': ' + str(data['currency']))
        except:
            return Markup("❓ <span class='text-info'>No data about Currency!")

    def currentPriceDiv(self):
        """ Current Stock Price """
        data = self.data
        try:
            currentPriceDiv = '{:,}'.format(round(data['currentPrice'], 2))
            return currentPriceDiv
        except:
            return Markup("❓ <span class='text-info'>No data about Current Price!")

    def returnOnEquity(self):
        """ Return on Equity """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.returnOnEquity[2] + ': ' + str(round(data['returnOnEquity'] * 100, 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about ROE")

    def returnOnAssets(self):
        """ Return on Assets """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.returnOnAssets[2] + ': ' + str(round(data['returnOnAssets'] * 100, 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about ROA!")

    def revenueGrowth(self):
        """ Revenue Growth """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.revenueGrowth[1] + ': ' + str(round(data['revenueGrowth'] * 100, 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Sales Growth!")

    def revenueQuarterlyGrowth(self):
        """ Quarterly Revenue Growth """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.revenueQuarterlyGrowth[1] + ': ' + str(data['revenueQuarterlyGrowth']) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Quarterly Sales Growth!")

    def earningsGrowth(self):
        """ Earnings Growth """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.earningsGrowth[1] + ': ' + str(round(data['earningsGrowth'] * 100, 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Earnings Growth!")

    def earningsQuarterlyGrowth(self):
        """ Quarterly Earnings Growth """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.earningsQuarterlyGrowth[1] + ': ' + str(round(data['earningsQuarterlyGrowth'] * 100, 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Quarterly Earnings Growth!")

    def grossMargins(self):
        """ Gross Margin """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.grossMargins[1] + ': ' + str(round(data['grossMargins'] * 100, 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Gross Margin!")

    def ebitdaMargins(self):
        """ EBITDA Margin """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.ebitdaMargins[1] + ': ' + str(round(data['ebitdaMargins'] * 100, 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about EBITDA Margin!")

    def operatingMargins(self):
        """ Operating Margin """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.operatingMargins[1] + ': ' + str(round(data['operatingMargins'] * 100, 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Operating Margin!")

    def profitMargins(self):
        """ Profit Margin """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.profitMargins[1] + ': ' + str(round(data['profitMargins'] * 100, 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Profit Margin!")

    def totalRevenue(self):
        """ Total Revenue """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.totalRevenue[1] + ': ' + str('{:,}'.format(round(strict_divide(data['totalRevenue'], 1000000000), 2))) + ' bln ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Total Revenue!")

    def revenuePerShare(self):
        """ Total Revenue (ps) """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.revenuePerShare[1] + ': ' + str(round(data['revenuePerShare'], 2)) + ' ' + data['currency'] + '/share')
        except:
            return Markup("❓ <span class='text-info'>No data about Total Revenue (ps)!")

    def grossProfits(self):
        """ Gross Profits """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.grossProfits[1] + ': ' + str('{:,}'.format(round(strict_divide(data['grossProfits'], 1000000000), 2))) + ' bln ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Gross Profits!")

    def ebitda(self):
        """ EBITDA """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.ebitda[1] + ': ' + str('{:,}'.format(round(strict_divide(data['ebitda'], 1000000000), 2))) + ' bln ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about EBITDA!")

    def netIncomeToCommon(self):
        """ Net Income To Common """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.netIncomeToCommon[1] + ': ' + str('{:,}'.format(round(strict_divide(data['netIncomeToCommon'], 1000000000), 2))) + ' bln ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Net Income To Common!")

    def trailingEps(self):
        """ Trailing Earnings per share """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.trailingEps[1] + ': ' + str(round(data['trailingEps'], 2)) + ' ' + data['currency'] + '/share')
        except:
            return Markup("❓ <span class='text-info'>No data about Trailing Earnings per share!")

    def forwardEps(self):
        """ Forward Earnings per share """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.forwardEps[1] + ': ' + str(round(data['forwardEps'], 2)) + ' ' + data['currency'] + '/share')
        except:
            return Markup("❓ <span class='text-info'>No data about Forward Earnings per share!")

    def operatingCashflow(self):
        """ Operating Cashflow """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.operatingCashflow[1] + ': ' + str('{:,}'.format(round(strict_divide(data['operatingCashflow'], 1000000000), 2))) + ' bln ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Operating Cashflow!")

    def freeCashflow(self):
        """ Free Cashflow """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.freeCashflow[1] + ': ' + str('{:,}'.format(round(strict_divide(data['freeCashflow'], 1000000000), 2))) + ' bln ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Free Cashflow!")

    def debtToEquity(self):
        """ Debt to Equity """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.debtToEquity[1] + ': ' + str(round(data['debtToEquity'], 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Debt to Equity (D/E)!")

    def totalCash(self):
        """ Total Cash """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.totalCash[1] + ': ' + str('{:,}'.format(round(strict_divide(data['totalCash'], 1000000000), 2))) + ' bln ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Total Cash!")

    def totalCashPerShare(self):
        """ Total Cash (ps)"""
        data = self.data
        d = Dictionary
        try:
            return Markup(d.totalCashPerShare[1] + ': ' + str(round(data['totalCashPerShare'], 2)) + ' ' + data['currency'] + '/share')
        except:
            return Markup("❓ <span class='text-info'>No data about Total Cash (ps)!")

    def totalDebt(self):
        """ Total Debt """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.totalDebt[1] + ': ' + str('{:,}'.format(round(strict_divide(data['totalDebt'], 1000000000), 2))) + ' bln ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Total Debt!")

    def bookValue(self):
        """ Bookvalue (ps) """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.bookValue[1] + ': ' + str(round(data['bookValue'], 2)) + ' ' + data['currency'] + '/share')
        except:
            return Markup("❓ <span class='text-info'>No data about Bookvalue (ps)!")

    def currentRatio(self):
        """ Current Ratio """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.currentRatio[1] + ': ' + str(round(data['currentRatio'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about Current Ratio!")

    def quickRatio(self):
        """ Quick Ratio """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.quickRatio[1].title() + ': ' + str(round(data['quickRatio'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about Quick Ratio!")

    def dividends(self):
        """ Payout Ratio """
        data = self.data
        d = Dictionary
        try:
            if data['payoutRatio'] != 0:
                return Markup(d.payoutRatio[1] + ': ' + str(round(data['payoutRatio'] * 100, 2)) + ' %<br>\t\t\t\t\t<li>' + d.lastDividendValue[1] + ': ' + str(data['lastDividendValue']) + ' ' + data['currency'] + '<br>\t\t\t\t\t<li>' + d.trailingAnnualDividendYield[1] + ': ' + str(round(data['trailingAnnualDividendYield'] * 100, 2)) + ' %<br>\t\t\t\t\t<li>' + d.dividendYield[1] + ': ' + str(round(data['dividendYield'] * 100, 2)) + ' %<br>\t\t\t\t\t<li>' + d.trailingAnnualDividendRate[1] + ': ' + str(data['trailingAnnualDividendRate']) + ' ' + data['currency'] + '/share<br>\t\t\t\t\t<li>' + d.dividendRate[1] + ': ' + str(data['dividendRate']) + ' ' + data['currency'] + '/share<br>\t\t\t\t\t<li>' + d.fiveYearAvgDividendYield[1] + ': ' + str(round(data['fiveYearAvgDividendYield'], 2)) + ' %')
            else:
                return Markup("<span class='text-danger'>The company does not pay dividends!")
        except:
            return Markup("❓ <span class='text-info'>No data about Dividends!")

    def marketCap(self):
        """ Market Capitalization """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.marketCap[1] + ': ' + str('{:,}'.format(round(strict_divide(data['marketCap'], 1000000000), 2))) + ' bln ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Market Capitalization!")

    def enterpriseValue(self):
        """ Enterprise value (EV) """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.enterpriseValue[1] + ': ' + str('{:,}'.format(round(strict_divide(data['enterpriseValue'], 1000000000), 2))) + ' bln ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Enterprise Value (EV)!")

    def enterpriseToRevenue(self):
        """ Enterprise value to Revenue """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.enterpriseToRevenue[2] + ': ' + str(round(data['enterpriseToRevenue'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about EV/Sales!")

    def enterpriseToEbitda(self):
        """ Enterprise value to EBITDA """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.enterpriseToEbitda[2] + ': ' + str(round(data['enterpriseToEbitda'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about EV/EBITDA!")

    def priceToBook(self):
        """ Price to Bookvalue """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.priceToBook[2] + ': ' + str(round(data['priceToBook'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about P/B!")

    def priceToSalesTrailing12Months(self):
        """ Trailing P/Sales ratio """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.priceToSalesTrailing12Months[2] + ': ' + str(round(data['priceToSalesTrailing12Months'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about Trailing P/Sales!")

    def trailingPE(self):
        """ Trailing P/E ratio """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.trailingPE[1] + ': ' + str(round(data['trailingPE'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about Trailing P/E!")

    def forwardPE(self):
        """ Forward P/E ratio """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.forwardPE[1] + ': ' + str(round(data['forwardPE'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about Forward P/E!")

    def trailingPegRatio(self):
        """ Trailing PEG ratio """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.trailingPegRatio[1] + ': ' + str(round(data['trailingPegRatio'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about Trailing PEG!")

    def pegRatio(self):
        """ Forward PEG ratio (fwd.) """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.pegRatio[1] + ': ' + str(round(data['pegRatio'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about Forward PEG!")

    def priceToBookValue(self):
        """ Price/Book Value < 1 = Cheap with respect to liquidation value (Book Value)! """
        data = self.data
        w = self.weights_list
        p = self.points_list
        try:
            if data['priceToBook'] > 1.5:
                w.append(Score.w_PB)
                p.append(Score.w_PB * Score.pf_neg)
                return Markup('⛔ P/BV > 1.5 (' + str(round(data['priceToBook'], 2)) + ")<br>\t\t\t\t\t<span class='text-danger'>↳ Expensive with respect to liquidation value!")
            if data['priceToBook'] >= 1 and data['priceToBook'] <= 1.5:
                return Markup('✅ P/BV between 1 à 1.5 (' + str(round(data['priceToBook'], 2)) + ")<br>\t\t\t\t\t<span class='text-secondary'>↳ Fairly valued!")
            if data['priceToBook'] < 1:
                w.append(Score.w_PB)
                p.append(Score.w_PB * Score.pf_pos)
                return Markup('✅ P/BV < 1 (' + str(round(data['priceToBook'], 2)) + ")<br>\t\t\t\t\t<span class='text-success'>↳ Cheap with respect to liquidation value!")
        except:
            return Markup("❓ <span class='text-info'>No data about P/B (ttm)!")

    def priceToEarningsTTM(self):
        """ Trailing PE > Forward PE = Tailwind expected earnings! """
        data = self.data
        w = self.weights_list
        p = self.points_list
        try:
            if data['trailingPE'] <= data['forwardPE']:
                w.append(Score.w_trailingPE)
                p.append(Score.w_trailingPE * Score.pf_neg)
                return Markup('⛔ Trailing P/E ≤ Forward P/E (' + str(round(data['trailingPE'], 2)) + ' ≤ ' + str(round(data['forwardPE'], 2)) + ")<br>\t\t\t\t\t<span class='text-danger'>↳ Headwind expected earnings!")
            if data['trailingPE'] > data['forwardPE']:
                w.append(Score.w_trailingPE)
                p.append(Score.w_trailingPE * Score.pf_pos)
                return Markup('✅ Trailing P/E > Forward P/E (' + str(round(data['trailingPE'], 2)) + ' > ' + str(round(data['forwardPE'], 2)) + ")<br>\t\t\t\t\t<span class='text-success'>↳ Tailwind expected earnings!")
        except:
            return Markup("❓ <span class='text-info'>No data about P/E (ttm)!")

    def priceToEarningsGrowthTTM(self):
        """ Trailing PEG > Forward PEG = Tailwind Business, as long as forward earnings growth will NOT decrease less than Forward PE! """
        data = self.data
        w = self.weights_list
        p = self.points_list
        try:
            if data['trailingPegRatio'] <= data['pegRatio']:
                w.append(Score.w_trailingPEG)
                p.append(Score.w_trailingPEG * Score.pf_neg)
                return Markup('⛔ Trailing PEG ≤ Forward PEG (' + str(round(data['trailingPegRatio'], 2)) + ' ≤ ' + str(round(data['pegRatio'], 2)) + ")<br>\t\t\t\t\t<span class='text-danger'>↳ Headwind Business Growth!")
            if data['trailingPegRatio'] > data['pegRatio']:
                w.append(Score.w_trailingPEG)
                p.append(Score.w_trailingPEG * Score.pf_pos)
                return Markup('✅ Trailing PEG > Forward PEG (' + str(round(data['trailingPegRatio'], 2)) + ' > ' + str(round(data['pegRatio'], 2)) + ")<br>\t\t\t\t\t<span class='text-success'>↳ Tailwind Business Growth!")
        except:
            return Markup("❓ <span class='text-info'>No data about PEG (ttm)!")

    def evToEbitda(self):
        """ EV/EBITDA < 4  = Cheap with respect to EBITDA! """
        data = self.data
        w = self.weights_list
        p = self.points_list
        try:
            if data['enterpriseToEbitda'] < 0:
                w.append(Score.w_EVEBITDA)
                p.append(Score.w_EVEBITDA * Score.pf_neg)
                return Markup('⛔ EV/EBITDA < 4 (' + str(round(data['enterpriseToEbitda'], 2)) + ")<br>\t\t\t\t\t<span class='text-success'>↳ Cheap with respect to EBITDA!")
            if data['enterpriseToEbitda'] >= 0 and data['enterpriseToEbitda'] < 4:
                w.append(Score.w_EVEBITDA)
                p.append(Score.w_EVEBITDA * Score.pf_pos)
                return Markup('✅ EV/EBITDA < 4 (' + str(round(data['enterpriseToEbitda'], 2)) + ")<br>\t\t\t\t\t<span class='text-success'>↳ Cheap with respect to EBITDA!")
            if data['enterpriseToEbitda'] >= 4:
                w.append(Score.w_EVEBITDA)
                p.append(Score.w_EVEBITDA * Score.pf_mod)
                return Markup('⛔ EV/EBITDA ≥ 4 (' + str(round(data['enterpriseToEbitda'], 2)) + ")<br>\t\t\t\t\t<span class='text-danger'>↳ Expensive with respect to EBITDA!")
        except:
            return Markup("❓ <span class='text-info'>No data about EV/EBITDA!")

    def beta(self):
        """ Beta (β) """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.beta[1] + ': ' + str(round(data['beta'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about Beta (β)!")

    def currentPrice(self):
        """ Current Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup("<span class='text-primary'>" + d.currentPrice[1] + ': ' + str('{:,}'.format(round(data['currentPrice'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Current Stock Price!")

    def fiftyTwoWeekHigh(self):
        """ 52w High Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup("<span class='text-primary'>" + d.fiftyTwoWeekHigh[1] + ': ' + str('{:,}'.format(round(data['fiftyTwoWeekHigh'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about 52w High Stock Price!")

    def fiftyTwoWeekLow(self):
        """ 52w Low Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup("<span class='text-primary'>" + d.fiftyTwoWeekLow[1] + ': ' + str('{:,}'.format(round(data['fiftyTwoWeekLow'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about 52w Low Stock Price!")

    def fiftyDayAverage(self):
        """ 50d Avg. Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.fiftyDayAverage[1] + ': ' + str('{:,}'.format(round(data['fiftyDayAverage'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about 50d Avg. Stock Price!")

    def twoHundredDayAverage(self):
        """ 200d Avg. Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.twoHundredDayAverage[1] + ': ' + str('{:,}'.format(round(data['twoHundredDayAverage'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about 200d Avg. Stock Price!")

    def previousClose(self):
        """ Previous Close Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.previousClose[1] + ': ' + str('{:,}'.format(round(data['previousClose'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Previous Close Stock Price!")

    def priceOpen(self):
        """ Open Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.priceOpen[1] + ': ' + str('{:,}'.format(round(data['open'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Open Stock Price!")

    def dayHigh(self):
        """ Day High Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.dayHigh[1] + ': ' + str('{:,}'.format(round(data['dayHigh'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Day High Stock Price!")

    def dayLow(self):
        """ Day Low Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.dayLow[1] + ': ' + str('{:,}'.format(round(data['dayLow'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Day Low Stock Price!")

    def ask(self):
        """ Ask Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.ask[1] + ': ' + str('{:,}'.format(round(data['ask'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Ask Stock Price!")

    def bid(self):
        """ Bid Stock Price """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.bid[1] + ': ' + str('{:,}'.format(round(data['bid'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Bid Stock Price!")

    def askSize(self):
        """ Ask Size """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.askSize[1].title() + ': ' + str('{:,}'.format(data['askSize'])))
        except:
            return Markup("❓ <span class='text-info'>No data about Ask Size!")

    def bidSize(self):
        """ Bid Size """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.bidSize[1].title() + ': ' + str('{:,}'.format(data['bidSize'])))
        except:
            return Markup("❓ <span class='text-info'>No data about Bid Size!")

    def heldPercentInsiders(self):
        """ Shares Held by Insiders (%) """
        data = self.data
        d = Dictionary
        try:
            return Markup("<span class='text-primary'>" + d.heldPercentInsiders[1] + ': ' + str(round(data['heldPercentInsiders'] * 100, 3)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Shares Held by Insiders (%)!")

    def heldPercentInstitutions(self):
        """ Shares Held by Institutions (%) """
        data = self.data
        d = Dictionary
        try:
            return Markup("<span class='text-primary'>" + d.heldPercentInstitutions[1] + ': ' + str(round(data['heldPercentInstitutions'] * 100, 3)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Shares Held by Institutions (%)!")

    def heldPercentIndividuals(self):
        """ Shares Held by Individuals (%) """
        data = self.data
        d = Dictionary
        try:
            sharesHeldByInstitutions = round(data['heldPercentInstitutions'] * 100, 3)
            sharesHeldByInsiders = round(data['heldPercentInsiders'] * 100, 3)
            sharesHeldByIndividuals = round(100 - (sharesHeldByInstitutions + sharesHeldByInsiders), 3)
            return Markup(d.heldPercentIndividuals[1] + ': ' + str(sharesHeldByIndividuals) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Shares Held by Individuals (%)!")

    def sharesOutstanding(self):
        """ Shares Outstanding """
        data = self.data
        d = Dictionary
        try:
            return Markup("<span class='text-primary'>" + d.sharesOutstanding[1] + ': ' + str('{:,}'.format(round(strict_divide(data['sharesOutstanding'], 1000000), 2))) + ' mln')
        except:
            return Markup("❓ <span class='text-info'>No data about Shares Outstanding!")

    def floatShares(self):
        """ Float Shares Outstanding """
        data = self.data
        d = Dictionary
        try:
            return Markup("<span class='text-primary'>" + d.floatShares[1] + ': ' + str('{:,}'.format(round(strict_divide(data['floatShares'], 1000000), 2))) + ' mln')
        except:
            return Markup("❓ <span class='text-info'>No data about Float Shares Outstanding!")

    def volume(self):
        """ Volume Shares Trading """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.volume[1] + ': ' + str('{:,}'.format(round(strict_divide(data['volume'], 1000000), 3))) + ' mln')
        except:
            return Markup("❓ <span class='text-info'>No data about Volume Shares Trading!")

    def averageVolume(self):
        """ Avg. Volume Shares Trading """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.averageVolume[1] + ': ' + str('{:,}'.format(round(strict_divide(data['averageVolume'], 1000000), 3))) + ' mln')
        except:
            return Markup("❓ <span class='text-info'>No data about Avg. Volume Shares Trading!")

    def averageDailyVolume10Day(self):
        """ Daily Avg. Volume Shares Trading (10d) """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.averageDailyVolume10Day[1] + ': ' + str('{:,}'.format(round(strict_divide(data['averageDailyVolume10Day'], 1000000), 3))) + ' mln')
        except:
            return Markup("❓ <span class='text-info'>No data about Daily Avg. Volume Shares Trading (10d)!")

    def averageDailyVolume10DayToSO(self):
        """ Daily Avg. Volume/Share Outstanding (10d) """
        data = self.data
        d = Dictionary
        try:
            averageDailyVolume10DayToSO = strict_divide(data['averageDailyVolume10Day'], data['sharesOutstanding']) * 100
            return Markup(d.averageDailyVolume10DayToSO[1] + ': ' + str(round(averageDailyVolume10DayToSO, 1)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Daily Avg. Volume/Share Outstanding (10d)!")

    def averageDailyVolume10DayToFloat(self):
        """ Daily Avg. Volume/Float (10d) """
        data = self.data
        d = Dictionary
        try:
            averageDailyVolume10DayToFloat = strict_divide(data['averageDailyVolume10Day'], data['sharesOutstanding']) * 100
            return Markup(d.averageDailyVolume10DayToFloat[1] + ': ' + str(round(averageDailyVolume10DayToFloat, 1)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Daily Avg. Volume/Float (10d)!")

    def lastSplitFactor(self):
        """ Last Split Factor Share Outstanding """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.lastSplitFactor[1] + ': ' + str(data['lastSplitFactor']))
        except:
            return Markup("❓ <span class='text-info'>No data about Last Split Factor Share Outstanding!")

    def tradeable(self):
        """ Options Treadable """
        data = self.data
        d = Dictionary
        try:
            if data['tradeable'] == True:
                return Markup(d.tradeable[1] + ': Yes')
            if data['tradeable'] == False:
                return Markup(d.tradeable[1] + ': No')
        except:
            return Markup("❓ <span class='text-info'>No data about Options Treadable!")

    def openInterest(self):
        """ Options Trading Open Interest """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.openInterest[1] + ': ' + str(data['openInterest']))
        except:
            return Markup("❓ <span class='text-info'>No data about Options Trading Open Interest!")

    def strikePrice(self):
        """ Options Trading Strike Price """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.strikePrice[1] + ': ' + str(data['strikePrice']))
        except:
            return Markup("❓ <span class='text-info'>No data about Options Trading Strike Price!")

    def shortRatio(self):
        """ Short Ratio """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.shortRatio[1].title() + ': ' + str(round(data['shortRatio'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about Short Ratio!")

    def shortPercentOfFloat(self):
        """ Short (%) Of Float """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.shortPercentOfFloat[1] + ': ' + str(round(data['shortPercentOfFloat'] * 100, 2)) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Short (%) Of Float!")

    def sharesShort(self):
        """ Short Shares Outstanding """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.sharesShort[1] + ': ' + str('{:,}'.format(round(strict_divide(data['sharesShort'], 1000000), 2))) + ' mln')
        except:
            return Markup("❓ <span class='text-info'>No data about Short Shares Outstanding!")

    def sharesShortPriorMonth(self):
        """ Short Shares Outstanding Prior Month """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.sharesShortPriorMonth[1] + ': ' + str(round(strict_divide(data['sharesShortPriorMonth'], 1000000), 2)) + ' mln')
        except:
            return Markup("❓ <span class='text-info'>No data about Short Shares Outstanding Prior Month!")

    def momentumDayTrading(self):
        """ Momentum DayTrading """
        data = self.data
        try:
            if data['currentPrice'] < data['open']:
                return Markup("⛔ Current Price < Open Price:<br>\t\t\t\t\t<span class='text-danger'>↳ Market is currently SELLING!")
            elif data['currentPrice'] > data['open']:
                return Markup("✅ Current Price > Open Price:<br>\t\t\t\t\t<span class='text-success'>↳ Market is currently BUYING!")
            elif data['askSize'] == 0 and data['bidSize'] == 0:
                return Markup("❓ Ask Size = Bid Size = 0:<br>\t\t\t\t\t<span class='text-secondary'>↳ Market is currently NOT TRADING!")
            elif data['currentPrice'] == data['open']:
                return Markup("⭕ Current Price = Open Price:<br>\t\t\t\t\t<span class='text-secondary'>↳ Market is currently UNCHANGED!")
        except:
            return Markup("❓ <span class='text-info'>No data about Momentum DayTrading!")

    def momentumDayTrading_BID_ASK(self):
        """ Momentum DayTrading """
        data = self.data
        try:
            if data['bidSize'] < data['askSize']:
                return Markup("⛔ Bid Size < Ask Size:<br>\t\t\t\t\t<span class='text-danger'>↳ Market is currently BEARISH (bid-ask)!")
            elif data['bidSize'] > data['askSize']:
                return Markup("✅ Bid Size > Ask Size:<br>\t\t\t\t\t<span class='text-success'>↳ Market is currently BULLISH (bid-ask)!")
            elif data['bidSize'] == 0 and data['askSize'] == 0:
                return Markup("❓ Bid Size = Ask Size = 0:<br>\t\t\t\t\t<span class='text-secondary'>↳ Market is currently NOT TRADING (bid-ask)!")
            elif data['bidSize'] == data['askSize']:
                return Markup("⭕ Bid Size = Ask Size:<br>\t\t\t\t\t<span class='text-secondary'>↳ Market is currently INDIFFERENT (bid-ask)!")
        except:
            return Markup("❓ <span class='text-info'>No data about Momentum DayTrading!")

    def momentum50d(self):
        """ Momentum 50d-Trading """
        data = self.data
        try:
            if data['currentPrice'] < data['fiftyDayAverage']:
                return Markup("⛔ Current Price < 50d Avg. Price:<br>\t\t\t\t\t<span class='text-danger'>↳ Stock is currently in a BEAR market (Avg. 50d)!")
            elif data['currentPrice'] > data['fiftyDayAverage']:
                return Markup("✅ Current Price > 50d Avg. Price:<br>\t\t\t\t\t<span class='text-success'>↳ Stock is currently in a BULL market (Avg. 50d)!")
            elif data['currentPrice'] == data['fiftyDayAverage']:
                return Markup("⭕ Current Price = 50d Avg. Price:<br>\t\t\t\t\t<span class='text-secondary'>↳ Market is currently UNCHANGED (Avg. 50d)!")
        except:
            return Markup("❓ <span class='text-info'>No data about Momentum 50d-Trading!")

    def momentum200d(self):
        """ Momentum 200d Trading """
        data = self.data
        try:
            if data['currentPrice'] < data['twoHundredDayAverage']:
                return Markup("⛔ Current Price < 200d Avg. Price:<br>\t\t\t\t\t<span class='text-danger'>↳ Stock is currently in a BEAR market (Avg. 200d)!")
            elif data['currentPrice'] > data['twoHundredDayAverage']:
                return Markup("✅ Current Price > 200d Avg. Price:<br>\t\t\t\t\t<span class='text-success'>↳ Stock is currently in a BULL market (Avg. 200d)!")
            elif data['currentPrice'] == data['twoHundredDayAverage']:
                return Markup("⭕ Current Price = 200d Avg. Price:<br>\t\t\t\t\t<span class='text-secondary'>↳ Market is currently UNCHANGED (Avg. 200d)!")
        except:
            return Markup("❓ <span class='text-info'>No data about Momentum 200d-Trading!")

    def numberOfAnalystOpinions(self):
        """ Analyst Opinions (N°) """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.numberOfAnalystOpinions[1] + ': ' + str(round(data['numberOfAnalystOpinions'], 2)))
        except:
            return Markup("❓ <span class='text-info'>No data about Analyst Opinions (N°)!")

    def recommendationKey(self):
        """ Analyst Recommendation """
        data = self.data
        d = Dictionary
        try:
            return Markup("<span class='text-primary'>" + d.recommendationKey[1] + ': ' + str(data['recommendationKey']))
        except:
            return Markup("❓ <span class='text-info'>No data about Analyst Recommendation!")

    def recommendationMean(self):
        """ Analyst Recommendation (mean) """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.recommendationMean[1] + ': ' + str(data['recommendationMean']))
        except:
            return Markup("❓ <span class='text-info'>No data about Analyst Recommendation (mean)!")

    def recommendations(self):
        """ Recommendations """
        try:
            stock = self.stock
            recom = stock.get_recommendations()
            recom = recom.reset_index()
            recomTail = recom.tail()
            recomTail = recomTail.sort_values(by='Date', ascending=False)
            recomTailFirm = list(recomTail['Firm'])
            recomTailToGrade = list(recomTail['To Grade'])
            recomTailDate = list(recomTail['Date'])
            recomList = []
            for d, f, g in zip(recomTailDate, recomTailFirm, recomTailToGrade):
                l = f'{f}: {g} ({d})'
                recomList.append(l)
            return Markup("<span class='text-primary'>" + recomList[0] + '<br>\t\t\t\t<li>' + recomList[1] + '<br>\t\t\t\t<li>' + recomList[2] + '<br>\t\t\t\t<li>' + recomList[3] + '<br>\t\t\t\t<li>' + recomList[4])
        except:
            return Markup("❓ <span class='text-info'>No data about Recommendations!")

    def analystAnalysis(self):
        """ Analyst Analysis #keys: 0Q, +1Q, 0Y, +1Y, -5Y, +5Y """
        growthRate_0q = self.growthRate_0q
        growthRate_n1q = self.growthRate_n1q
        growthRate_0y = self.growthRate_0y
        growthRate_n1y = self.growthRate_n1y
        growthRate_p5y = self.growthRate_p5y
        growthRate_n5y = self.growthRate_n5y
        try:
            return Markup('Growth rate current quarter: ' + str(round(growthRate_0q * 100, 2)) + ' %<br><li>Growth rate next quarter: ' + str(round(growthRate_n1q * 100, 2)) + ' %<br><li>Growth rate current year: ' + str(round(growthRate_0y * 100, 2)) + ' %<br><li>Growth rate next year: ' + str(round(growthRate_n1y * 100, 2)) + " %<br><li><span class='text-primary'>Growth rate past 5 years: " + str(round(growthRate_p5y * 100, 2)) + " % per annum<br><li><span class='text-primary'>Growth rate next 5 years: " + str(round(growthRate_n5y * 100, 2)) + ' % per annum')
        except:
            return Markup("❓ <span class='text-info'>No data about Analyst Analysis!")

    def targetHighPrice(self):
        """ Analyst Target Price High """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.targetHighPrice[1] + ': ' + str('{:,}'.format(round(data['targetHighPrice'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Analyst Target Price High!")

    def targetMedianPrice(self):
        """ Analyst Target Price Median """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.targetMedianPrice[1] + ': ' + str('{:,}'.format(round(data['targetMedianPrice'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Analyst Target Price Median!")

    def targetLowPrice(self):
        """ Analyst Target Price Low """
        data = self.data
        d = Dictionary
        try:
            return Markup(d.targetLowPrice[1] + ': ' + str('{:,}'.format(round(data['targetLowPrice'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Analyst Target Price Low!")

    def targetMeanPrice(self):
        """ Analyst Target Price Mean """
        data = self.data
        d = Dictionary
        try:
            return Markup("<span class='text-primary'>" + d.targetMeanPrice[1] + ': ' + str('{:,}'.format(round(data['targetMeanPrice'], 2))) + ' ' + data['currency'])
        except:
            return Markup("❓ <span class='text-info'>No data about Analyst Target Price Mean!")

    def estimatedReturnHigh(self):
        """ Estimated Return (High) """
        data = self.data
        d = Dictionary
        try:
            estimatedReturnHigh = round((strict_divide(data['targetHighPrice'], data['currentPrice']) - 1) * 100, 2)
            return Markup('Estimated Return (High): ' + str(estimatedReturnHigh) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Estimated Return (High)!")

    def estimatedReturnMedian(self):
        """ Estimated Return (Median) """
        data = self.data
        d = Dictionary
        try:
            estimatedReturnMedian = round((strict_divide(data['targetMedianPrice'], data['currentPrice']) - 1) * 100, 2)
            return Markup('Estimated Return (Median): ' + str(estimatedReturnMedian) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Estimated Return (Median)!")

    def estimatedReturnLow(self):
        """ Estimated Return (Low) """
        data = self.data
        d = Dictionary
        try:
            estimatedReturnLow = round((strict_divide(data['targetLowPrice'], data['currentPrice']) - 1) * 100, 2)
            return Markup('Estimated Return (Low): ' + str(estimatedReturnLow) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Estimated Return (Low)!")

    def estimatedReturnMean(self):
        """ Estimated Return (Mean) """
        data = self.data
        d = Dictionary
        try:
            estimatedReturnMean = round((strict_divide(data['targetMeanPrice'], data['currentPrice']) - 1) * 100, 2)
            return Markup("<span class='text-primary'>Estimated Return (Mean): " + str(estimatedReturnMean) + ' %')
        except:
            return Markup("❓ <span class='text-info'>No data about Estimated Return (Mean)!")

    def returnOnEquityHistory(self):
        """ ROE: net earnings/equity = ROE > 15% """
        data = self.data
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            if data['returnOnEquity'] != None:
                net_income_y0 = self._cell(pal_t, 'Net Income', 0)
                net_income_y1 = self._cell(pal_t, 'Net Income', 1)
                net_income_y2 = self._cell(pal_t, 'Net Income', 2)
                net_income_y3 = self._cell(pal_t, 'Net Income', 3)
                equity_y0 = self._cell(bs_t, 'Total Stockholder Equity', 0)
                equity_y1 = self._cell(bs_t, 'Total Stockholder Equity', 1)
                equity_y2 = self._cell(bs_t, 'Total Stockholder Equity', 2)
                equity_y3 = self._cell(bs_t, 'Total Stockholder Equity', 3)
                roe_ttm = round(data['returnOnEquity'] * 100, 2)
                roe_y0 = round(strict_divide(net_income_y0, equity_y0) * 100, 2)
                roe_y1 = round(strict_divide(net_income_y1, equity_y1) * 100, 2)
                roe_y2 = round(strict_divide(net_income_y2, equity_y2) * 100, 2)
                roe_y3 = round(strict_divide(net_income_y3, equity_y3) * 100, 2)
                if equity_y0 <= 0 or equity_y1 <= 0 or equity_y2 <= 0 or (equity_y3 <= 0):
                    self.fundamentals['returnOnEquityHistory'] = ([], [])
                    w.append(Score.w_ROE)
                    p.append(Score.w_ROE * Score.pf_mod)
                    return Markup("⛔ ROE: Denominator ≤ 0 !<br>\t\t\t\t\t\t<span class='text-danger'>↳ ROE not calculated.")
                else:
                    self.fundamentals['returnOnEquityHistory'] = ([self.y3, self.y2, self.y1, self.y0, self.ttm], [roe_y3, roe_y2, roe_y1, roe_y0, roe_ttm])
                    if (roe_ttm <= 15 or roe_y0 <= 15 or roe_y1 <= 15 or (roe_y2 <= 15) or (roe_y3 <= 15)) and (roe_ttm > roe_y0 and roe_y0 > roe_y1 and (roe_y1 > roe_y2) and (roe_y2 > roe_y3)):
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_mod)
                        w.append(Score.w_ROE_increasing)
                        p.append(Score.w_ROE_increasing * Score.pf_pos)
                        return Markup("⛔ ROE ≤ 15%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + '%, ' + str(roe_ttm) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ although: ROE consistently increasing")
                    elif (roe_ttm <= 15 or roe_y0 <= 15 or roe_y1 <= 15 or (roe_y2 <= 15) or (roe_y3 <= 15)) and roe_ttm > 15:
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_mod)
                        return Markup("⛔ ROE ≤ 15%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + '%, ' + str(roe_ttm) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ although: ROE " + str(self.ttm) + ' ≥ 15% (' + str(roe_ttm) + '%)')
                    elif roe_ttm <= 15 or roe_y0 <= 15 or roe_y1 <= 15 or (roe_y2 <= 15) or (roe_y3 <= 15):
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_neg)
                        return Markup("⛔ ROE ≤ 15%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + '%, ' + str(roe_ttm) + '%')
                    elif (roe_ttm > 15 and roe_y0 > 15 and (roe_y1 > 15) and (roe_y2 > 15) and (roe_y3 > 15)) and (roe_ttm > roe_y0 and roe_y0 > roe_y1 and (roe_y1 > roe_y2) and (roe_y2 > roe_y3)):
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_pos)
                        w.append(Score.w_ROE_increasing)
                        p.append(Score.w_ROE_increasing * Score.pf_pos)
                        return Markup("✅ ROE > 15%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + '%, ' + str(roe_ttm) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ ROE consistently increasing")
                    elif (roe_ttm > 15 and roe_y0 > 15 and (roe_y1 > 15) and (roe_y2 > 15) and (roe_y3 > 15)) and (roe_ttm < roe_y0 and roe_y0 < roe_y1 and (roe_y1 < roe_y2) and (roe_y2 < roe_y3)):
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_pos)
                        w.append(Score.w_ROE_decreasing)
                        p.append(Score.w_ROE_decreasing * Score.pf_neg)
                        return Markup("✅ ROE > 15%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + '%, ' + str(roe_ttm) + "%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: ROE consistently decreasing")
                    elif roe_ttm > 15 and roe_y0 > 15 and (roe_y1 > 15) and (roe_y2 > 15) and (roe_y3 > 15):
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_pos)
                        return Markup("✅ ROE > 15%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + '%, ' + str(roe_ttm) + '%')
            else:
                net_income_y0 = self._cell(pal_t, 'Net Income', 0)
                net_income_y0 = self._cell(pal_t, 'Net Income', 0)
                net_income_y1 = self._cell(pal_t, 'Net Income', 1)
                net_income_y2 = self._cell(pal_t, 'Net Income', 2)
                net_income_y3 = self._cell(pal_t, 'Net Income', 3)
                equity_y0 = self._cell(bs_t, 'Total Stockholder Equity', 0)
                equity_y1 = self._cell(bs_t, 'Total Stockholder Equity', 1)
                equity_y2 = self._cell(bs_t, 'Total Stockholder Equity', 2)
                equity_y3 = self._cell(bs_t, 'Total Stockholder Equity', 3)
                roe_y0 = round(strict_divide(net_income_y0, equity_y0) * 100, 2)
                roe_y1 = round(strict_divide(net_income_y1, equity_y1) * 100, 2)
                roe_y2 = round(strict_divide(net_income_y2, equity_y2) * 100, 2)
                roe_y3 = round(strict_divide(net_income_y3, equity_y3) * 100, 2)
                if equity_y0 <= 0 or equity_y1 <= 0 or equity_y2 <= 0 or (equity_y3 <= 0):
                    self.fundamentals['returnOnEquityHistory'] = ([], [])
                    w.append(Score.w_ROE)
                    p.append(Score.w_ROE * Score.pf_mod)
                    return Markup("⛔ ROE: Denominator ≤ 0 !<br>\t\t\t\t\t\t<span class='text-danger'>↳ ROE not calculated.")
                else:
                    self.fundamentals['returnOnEquityHistory'] = ([self.y3, self.y2, self.y1, self.y0], [roe_y3, roe_y2, roe_y1, roe_y0])
                    if (roe_y0 <= 15 or roe_y1 <= 15 or roe_y2 <= 15 or (roe_y3 <= 15)) and (roe_y0 > roe_y1 and roe_y1 > roe_y2 and (roe_y2 > roe_y3)):
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_mod)
                        w.append(Score.w_ROE_increasing)
                        p.append(Score.w_ROE_increasing * Score.pf_pos)
                        return Markup("⛔ ROE ≤ 15%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ although: ROE consistently increasing")
                    elif (roe_y0 <= 15 or roe_y1 <= 15 or roe_y2 <= 15 or (roe_y3 <= 15)) and roe_y0 > 15:
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_mod)
                        return Markup("⛔ ROE ≤ 15%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ although: ROE " + str(self.y0) + ' > 15% (' + str(roe_y0) + '%)')
                    elif roe_y0 <= 15 or roe_y1 <= 15 or roe_y2 <= 15 or (roe_y3 <= 15):
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_neg)
                        return Markup("⛔ ROE ≤ 15%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + '%')
                    elif (roe_y0 > 15 and roe_y1 > 15 and (roe_y2 > 15) and (roe_y3 > 15)) and (roe_y0 > roe_y1 and roe_y1 > roe_y2 and (roe_y2 > roe_y3)):
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_pos)
                        w.append(Score.w_ROE_increasing)
                        p.append(Score.w_ROE_increasing * Score.pf_pos)
                        return Markup("✅ ROE > 15%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ ROE consistently increasing")
                    elif (roe_y0 > 15 and roe_y1 > 15 and (roe_y2 > 15) and (roe_y3 > 15)) and (roe_y0 < roe_y1 and roe_y1 < roe_y2 and (roe_y2 < roe_y3)):
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_pos)
                        w.append(Score.w_ROE_decreasing)
                        p.append(Score.w_ROE_decreasing * Score.pf_neg)
                        return Markup("✅ ROE > 15%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: ROE consistently decreasing")
                    elif roe_y0 > 15 and roe_y1 > 15 and (roe_y2 > 15) and (roe_y3 > 15):
                        w.append(Score.w_ROE)
                        p.append(Score.w_ROE * Score.pf_pos)
                        return Markup("✅ ROE > 15%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roe_y3) + '%, ' + str(roe_y2) + '%, ' + str(roe_y1) + '%, ' + str(roe_y0) + '%')
        except:
            w.append(Score.w_ROE)
            p.append(Score.w_ROE * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about ROE!")

    def returnOnNetTangibleAssetsHistory(self):
        """ RONTA: net earnings/net tangible assets = RONTA > 1% (financials) """
        data = self.data
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            net_income_y0 = self._cell(pal_t, 'Net Income', 0)
            net_income_y1 = self._cell(pal_t, 'Net Income', 1)
            net_income_y2 = self._cell(pal_t, 'Net Income', 2)
            net_income_y3 = self._cell(pal_t, 'Net Income', 3)
            net_tangible_assets_y0 = self._cell(bs_t, 'Net Tangible Assets', 0)
            net_tangible_assets_y1 = self._cell(bs_t, 'Net Tangible Assets', 1)
            net_tangible_assets_y2 = self._cell(bs_t, 'Net Tangible Assets', 2)
            net_tangible_assets_y3 = self._cell(bs_t, 'Net Tangible Assets', 3)
            ronta_y0 = round(strict_divide(net_income_y0, net_tangible_assets_y0) * 100, 2)
            ronta_y1 = round(strict_divide(net_income_y1, net_tangible_assets_y1) * 100, 2)
            ronta_y2 = round(strict_divide(net_income_y2, net_tangible_assets_y2) * 100, 2)
            ronta_y3 = round(strict_divide(net_income_y3, net_tangible_assets_y3) * 100, 2)
            if net_tangible_assets_y0 <= 0 or net_tangible_assets_y1 <= 0 or net_tangible_assets_y2 <= 0 or (net_tangible_assets_y3 <= 0):
                self.fundamentals['returnOnNetTangibleAssetsHistory'] = ([], [])
                w.append(Score.w_RONTA)
                p.append(Score.w_RONTA * Score.pf_mod)
                return Markup("⛔ RONTA: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ RONTA not calculated.")
            else:
                self.fundamentals['returnOnNetTangibleAssetsHistory'] = ([self.y3, self.y2, self.y1, self.y0], [ronta_y3, ronta_y2, ronta_y1, ronta_y0])
                if (ronta_y0 <= 15 or ronta_y1 <= 15 or ronta_y2 <= 15 or (ronta_y3 <= 15)) and (ronta_y0 > ronta_y1 and ronta_y1 > ronta_y2 and (ronta_y2 > ronta_y3)):
                    w.append(Score.w_RONTA)
                    p.append(Score.w_RONTA * Score.pf_mod)
                    w.append(Score.w_RONTA_increasing)
                    p.append(Score.w_RONTA_increasing * Score.pf_pos)
                    return Markup("⛔ RONTA ≤ 15%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(ronta_y3) + '%, ' + str(ronta_y2) + '%, ' + str(ronta_y1) + '%, ' + str(ronta_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: RONTA consistently increasing")
                elif (ronta_y0 <= 15 or ronta_y1 <= 15 or ronta_y2 <= 15 or (ronta_y3 <= 15)) and ronta_y0 > 15:
                    w.append(Score.w_RONTA)
                    p.append(Score.w_RONTA * Score.pf_mod)
                    return Markup("⛔ RONTA ≤ 15%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(ronta_y3) + '%, ' + str(ronta_y2) + '%, ' + str(ronta_y1) + '%, ' + str(ronta_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: RONTA " + str(self.y0) + ' > 15% (' + str(ronta_y0) + '%)')
                elif ronta_y0 <= 15 or ronta_y1 <= 15 or ronta_y2 <= 15 or (ronta_y3 <= 15):
                    w.append(Score.w_RONTA)
                    p.append(Score.w_RONTA * Score.pf_neg)
                    return Markup("⛔ RONTA ≤ 15%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(ronta_y3) + '%, ' + str(ronta_y2) + '%, ' + str(ronta_y1) + '%, ' + str(ronta_y0) + '%')
                elif (ronta_y0 > 15 and ronta_y1 > 15 and (ronta_y2 > 15) and (ronta_y3 > 15)) and (ronta_y0 > ronta_y1 and ronta_y1 > ronta_y2 and (ronta_y2 > ronta_y3)):
                    w.append(Score.w_RONTA)
                    p.append(Score.w_RONTA * Score.pf_pos)
                    w.append(Score.w_RONTA_increasing)
                    p.append(Score.w_RONTA_increasing * Score.pf_pos)
                    return Markup("✅ RONTA > 15%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(ronta_y3) + '%, ' + str(ronta_y2) + '%, ' + str(ronta_y1) + '%, ' + str(ronta_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ RONTA consistently increasing")
                elif (ronta_y0 > 15 and ronta_y1 > 15 and (ronta_y2 > 15) and (ronta_y3 > 15)) and (ronta_y0 < ronta_y1 and ronta_y1 < ronta_y2 and (ronta_y2 < ronta_y3)):
                    w.append(Score.w_RONTA)
                    p.append(Score.w_RONTA * Score.pf_pos)
                    w.append(Score.w_RONTA_decreasing)
                    p.append(Score.w_RONTA_decreasing * Score.pf_neg)
                    return Markup("✅ RONTA > 15%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(ronta_y3) + '%, ' + str(ronta_y2) + '%, ' + str(ronta_y1) + '%, ' + str(ronta_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: RONTA consistently decreasing")
                elif ronta_y0 > 15 and ronta_y1 > 15 and (ronta_y2 > 15) and (ronta_y3 > 15):
                    w.append(Score.w_RONTA)
                    p.append(Score.w_RONTA * Score.pf_pos)
                    return Markup("✅ RONTA > 15%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(ronta_y3) + '%, ' + str(ronta_y2) + '%, ' + str(ronta_y1) + '%, ' + str(ronta_y0) + '%')
        except:
            w.append(Score.w_RONTA)
            p.append(Score.w_RONTA * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about RONTA!")

    def returnOnAssetsHistory(self):
        """ ROA: net earnings/total assets = ROA > 1% (financials) """
        data = self.data
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            if data['returnOnAssets'] != None:
                net_income_y0 = self._cell(pal_t, 'Net Income', 0)
                net_income_y1 = self._cell(pal_t, 'Net Income', 1)
                net_income_y2 = self._cell(pal_t, 'Net Income', 2)
                net_income_y3 = self._cell(pal_t, 'Net Income', 3)
                total_assets_y0 = self._cell(bs_t, 'Total Assets', 0)
                total_assets_y1 = self._cell(bs_t, 'Total Assets', 1)
                total_assets_y2 = self._cell(bs_t, 'Total Assets', 2)
                total_assets_y3 = self._cell(bs_t, 'Total Assets', 3)
                roa_ttm = round(data['returnOnAssets'] * 100, 2)
                roa_y0 = round(strict_divide(net_income_y0, total_assets_y0) * 100, 2)
                roa_y1 = round(strict_divide(net_income_y1, total_assets_y1) * 100, 2)
                roa_y2 = round(strict_divide(net_income_y2, total_assets_y2) * 100, 2)
                roa_y3 = round(strict_divide(net_income_y3, total_assets_y3) * 100, 2)
                if total_assets_y0 <= 0 or total_assets_y1 <= 0 or total_assets_y2 <= 0 or (total_assets_y3 <= 0):
                    self.fundamentals['returnOnAssetsHistory'] = ([], [])
                    w.append(Score.w_ROA)
                    p.append(Score.w_ROA * Score.pf_mod)
                    return Markup("⛔ ROA: Denominator ≤ 0 !<br>\t\t\t\t\t\t<span class='text-danger'>↳ ROA not calculated.")
                else:
                    self.fundamentals['returnOnAssetsHistory'] = ([self.y3, self.y2, self.y1, self.y0, self.ttm], [roa_y3, roa_y2, roa_y1, roa_y0, roa_ttm])
                    if (roa_ttm <= 1 or roa_y0 <= 1 or roa_y1 <= 1 or (roa_y2 <= 1) or (roa_y3 <= 1)) and (roa_ttm > roa_y0 and roa_y0 > roa_y1 and (roa_y1 > roa_y2) and (roa_y2 > roa_y3)):
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_mod)
                        w.append(Score.w_ROA_increasing)
                        p.append(Score.w_ROA_increasing * Score.pf_pos)
                        return Markup("⛔ ROA ≤ 1%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + '%, ' + str(roa_ttm) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ although: ROA consistently increasing")
                    elif (roa_ttm <= 1 or roa_y0 <= 1 or roa_y1 <= 1 or (roa_y2 <= 1) or (roa_y3 <= 1)) and roa_ttm > 1:
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_mod)
                        return Markup("⛔ ROA ≤ 1%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + '%, ' + str(roa_ttm) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ although: ROA " + str(self.ttm) + ' > 1% (' + str(roa_ttm) + '%)')
                    elif roa_ttm <= 1 or roa_y0 <= 1 or roa_y1 <= 1 or (roa_y2 <= 1) or (roa_y3 <= 1):
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_neg)
                        return Markup("⛔ ROA ≤ 1%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + '%, ' + str(roa_ttm) + '%')
                    elif (roa_ttm > 1 and roa_y0 > 1 and (roa_y1 > 1) and (roa_y2 > 1) and (roa_y3 > 1)) and (roa_ttm > roa_y0 and roa_y0 > roa_y1 and (roa_y1 > roa_y2) and (roa_y2 > roa_y3)):
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_pos)
                        w.append(Score.w_ROA_increasing)
                        p.append(Score.w_ROA_increasing * Score.pf_pos)
                        return Markup("✅ ROA > 1%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + '%, ' + str(roa_ttm) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ ROA consistently increasing")
                    elif (roa_ttm > 1 and roa_y0 > 1 and (roa_y1 > 1) and (roa_y2 > 1) and (roa_y3 > 1)) and (roa_ttm < roa_y0 and roa_y0 < roa_y1 and (roa_y1 < roa_y2) and (roa_y2 < roa_y3)):
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_pos)
                        w.append(Score.w_ROA_decreasing)
                        p.append(Score.w_ROA_decreasing * Score.pf_neg)
                        return Markup("✅ ROA > 1%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + '%, ' + str(roa_ttm) + "%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: ROA consistently decreasing")
                    elif roa_ttm > 1 and roa_y0 > 1 and (roa_y1 > 1) and (roa_y2 > 1) and (roa_y3 > 1):
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_pos)
                        return Markup("✅ ROA > 1%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + '%, ' + str(roa_ttm) + '%')
            else:
                net_income_y0 = self._cell(pal_t, 'Net Income', 0)
                net_income_y1 = self._cell(pal_t, 'Net Income', 1)
                net_income_y2 = self._cell(pal_t, 'Net Income', 2)
                net_income_y3 = self._cell(pal_t, 'Net Income', 3)
                total_assets_y0 = self._cell(bs_t, 'Total Assets', 0)
                total_assets_y1 = self._cell(bs_t, 'Total Assets', 1)
                total_assets_y2 = self._cell(bs_t, 'Total Assets', 2)
                total_assets_y3 = self._cell(bs_t, 'Total Assets', 3)
                roa_y0 = round(strict_divide(net_income_y0, total_assets_y0) * 100, 2)
                roa_y1 = round(strict_divide(net_income_y1, total_assets_y1) * 100, 2)
                roa_y2 = round(strict_divide(net_income_y2, total_assets_y2) * 100, 2)
                roa_y3 = round(strict_divide(net_income_y3, total_assets_y3) * 100, 2)
                if total_assets_y0 <= 0 or total_assets_y1 <= 0 or total_assets_y2 <= 0 or (total_assets_y3 <= 0):
                    self.fundamentals['returnOnAssetsHistory'] = ([], [])
                    w.append(Score.w_ROA)
                    p.append(Score.w_ROA * Score.pf_mod)
                    return Markup("⛔ ROA: Denominator ≤ 0 !<br>\t\t\t\t\t\t<span class='text-danger'>↳ ROA not calculated.")
                else:
                    self.fundamentals['returnOnAssetsHistory'] = ([self.y3, self.y2, self.y1, self.y0], [roa_y3, roa_y2, roa_y1, roa_y0])
                    if (roa_y0 <= 1 or roa_y1 <= 1 or roa_y2 <= 1 or (roa_y3 <= 1)) and (roa_y0 > roa_y1 and roa_y1 > roa_y2 and (roa_y2 > roa_y3)):
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_mod)
                        w.append(Score.w_ROA_increasing)
                        p.append(Score.w_ROA_increasing * Score.pf_pos)
                        return Markup("⛔ ROA ≤ 1%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ although: ROA consistently increasing")
                    elif (roa_y0 <= 1 or roa_y1 <= 1 or roa_y2 <= 1 or (roa_y3 <= 1)) and roa_y0 > 1:
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_mod)
                        return Markup("⛔ ROA ≤ 1%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ although: ROA " + str(self.y0) + ' > 1% (' + str(roa_y0) + '%)')
                    elif roa_y0 <= 1 or roa_y1 <= 1 or roa_y2 <= 1 or (roa_y3 <= 1):
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_neg)
                        return Markup("⛔ ROA ≤ 1%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + '%')
                    elif (roa_y0 > 1 and roa_y1 > 1 and (roa_y2 > 1) and (roa_y3 > 1)) and (roa_y0 > roa_y1 and roa_y1 > roa_y2 and (roa_y2 > roa_y3)):
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_pos)
                        w.append(Score.w_ROA_increasing)
                        p.append(Score.w_ROA_increasing * Score.pf_pos)
                        return Markup("✅ ROA > 1%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ ROA consistently increasing")
                    elif (roa_y0 > 1 and roa_y1 > 1 and (roa_y2 > 1) and (roa_y3 > 1)) and (roa_y0 < roa_y1 and roa_y1 < roa_y2 and (roa_y2 < roa_y3)):
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_pos)
                        w.append(Score.w_ROA_decreasing)
                        p.append(Score.w_ROA_decreasing * Score.pf_neg)
                        return Markup("✅ ROA > 1%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: ROA consistently decreasing")
                    elif roa_y0 > 1 and roa_y1 > 1 and (roa_y2 > 1) and (roa_y3 > 1):
                        w.append(Score.w_ROA)
                        p.append(Score.w_ROA * Score.pf_pos)
                        return Markup("✅ ROA > 1%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(roa_y3) + '%, ' + str(roa_y2) + '%, ' + str(roa_y1) + '%, ' + str(roa_y0) + '%')
        except:
            w.append(Score.w_ROA)
            p.append(Score.w_ROA * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about ROA!")

    def daysInventoryOnHandHistory(self):
        """ Days Inventory On Hand (DIOH) = (365*Avg.Inventory)/COGS: as low as possible = fast inventory turnover
			<span class='text-info'>No data about inventory 6y ago! """
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            inv_y0 = self._cell(bs_t, 'Inventory', 0)
            inv_y1 = self._cell(bs_t, 'Inventory', 1)
            inv_y2 = self._cell(bs_t, 'Inventory', 2)
            inv_y3 = self._cell(bs_t, 'Inventory', 3)
            cogs_y0 = self._cell(pal_t, 'Cost Of Revenue', 0)
            cogs_y1 = self._cell(pal_t, 'Cost Of Revenue', 1)
            cogs_y2 = self._cell(pal_t, 'Cost Of Revenue', 2)
            cogs_y3 = self._cell(pal_t, 'Cost Of Revenue', 3)
            days_inv_on_hand_y0 = round(strict_divide(365 * strict_divide(inv_y0 + inv_y1, 2), cogs_y0), 2)
            days_inv_on_hand_y1 = round(strict_divide(365 * strict_divide(inv_y1 + inv_y2, 2), cogs_y1), 2)
            days_inv_on_hand_y2 = round(strict_divide(365 * strict_divide(inv_y2 + inv_y3, 2), cogs_y2), 2)
            days_inv_on_hand_y3 = round(strict_divide(365 * inv_y3, cogs_y3), 2)
            if cogs_y0 <= 0 or cogs_y1 <= 0 or cogs_y2 <= 0 or (cogs_y3 <= 0):
                self.fundamentals['daysInventoryOnHandHistory'] = ([], [])
                w.append(Score.w_DIOH)
                p.append(Score.w_DIOH * Score.pf_mod)
                return Markup("⛔ Days Inventory On Hand: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ DIOH not calculated.")
            else:
                self.fundamentals['daysInventoryOnHandHistory'] = ([self.y3, self.y2, self.y1, self.y0], [days_inv_on_hand_y3, days_inv_on_hand_y2, days_inv_on_hand_y1, days_inv_on_hand_y0])
                if (days_inv_on_hand_y0 > days_inv_on_hand_y1 or days_inv_on_hand_y1 > days_inv_on_hand_y2 or days_inv_on_hand_y2 > days_inv_on_hand_y3) and days_inv_on_hand_y0 < days_inv_on_hand_y3:
                    w.append(Score.w_DIOH)
                    p.append(Score.w_DIOH * Score.pf_mod)
                    return Markup("⛔ Days Inventory On Hand not consistently decreasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(days_inv_on_hand_y3) + ' days, ' + str(days_inv_on_hand_y2) + ' days, ' + str(days_inv_on_hand_y1) + ' days, ' + str(days_inv_on_hand_y0) + " days<br>\t\t\t\t\t\t<span class='text-success'>↳ although: DIOH " + str(self.y3) + ' > ' + str(self.y0) + ' (' + str(days_inv_on_hand_y3) + ' > ' + str(days_inv_on_hand_y0) + ' days)')
                elif days_inv_on_hand_y0 > days_inv_on_hand_y1 or days_inv_on_hand_y1 > days_inv_on_hand_y2 or days_inv_on_hand_y2 > days_inv_on_hand_y3:
                    w.append(Score.w_DIOH)
                    p.append(Score.w_DIOH * Score.pf_neg)
                    return Markup("⛔ Days Inventory On Hand not consistently decreasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(days_inv_on_hand_y3) + ' days, ' + str(days_inv_on_hand_y2) + ' days, ' + str(days_inv_on_hand_y1) + ' days, ' + str(days_inv_on_hand_y0) + ' days')
                elif days_inv_on_hand_y0 <= days_inv_on_hand_y1 and days_inv_on_hand_y1 <= days_inv_on_hand_y2 and (days_inv_on_hand_y2 <= days_inv_on_hand_y3):
                    w.append(Score.w_DIOH)
                    p.append(Score.w_DIOH * Score.pf_pos)
                    return Markup("✅ Days Inventory On Hand consistently decreasing!<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(days_inv_on_hand_y3) + ' days, ' + str(days_inv_on_hand_y2) + ' days, ' + str(days_inv_on_hand_y1) + ' days, ' + str(days_inv_on_hand_y0) + ' days')
        except:
            w.append(Score.w_DIOH)
            p.append(Score.w_DIOH * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Days Inventory On Hand!")

    def inventoryTurnoverHistory(self):
        """ Inventory Turnover Rate (ITR) = COGS/Avg. Inventory: as high as possible """
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            inv_y0 = self._cell(bs_t, 'Inventory', 0)
            inv_y1 = self._cell(bs_t, 'Inventory', 1)
            inv_y2 = self._cell(bs_t, 'Inventory', 2)
            inv_y3 = self._cell(bs_t, 'Inventory', 3)
            cogs_y0 = self._cell(pal_t, 'Cost Of Revenue', 0)
            cogs_y1 = self._cell(pal_t, 'Cost Of Revenue', 1)
            cogs_y2 = self._cell(pal_t, 'Cost Of Revenue', 2)
            cogs_y3 = self._cell(pal_t, 'Cost Of Revenue', 3)
            days_inv_on_hand_y0 = round(strict_divide(365 * strict_divide(inv_y0 + inv_y1, 2), cogs_y0), 2)
            days_inv_on_hand_y1 = round(strict_divide(365 * strict_divide(inv_y1 + inv_y2, 2), cogs_y1), 2)
            days_inv_on_hand_y2 = round(strict_divide(365 * strict_divide(inv_y2 + inv_y3, 2), cogs_y2), 2)
            days_inv_on_hand_y3 = round(strict_divide(365 * inv_y3, cogs_y3), 2)
            inv_turnover_y0 = round(strict_divide(365, days_inv_on_hand_y0), 2)
            inv_turnover_y1 = round(strict_divide(365, days_inv_on_hand_y1), 2)
            inv_turnover_y2 = round(strict_divide(365, days_inv_on_hand_y2), 2)
            inv_turnover_y3 = round(strict_divide(365, days_inv_on_hand_y3), 2)
            if cogs_y0 <= 0 or cogs_y1 <= 0 or cogs_y2 <= 0 or (cogs_y3 <= 0):
                self.fundamentals['inventoryTurnoverHistory'] = ([], [])
                w.append(Score.w_ITR)
                p.append(Score.w_ITR * Score.pf_mod)
                return Markup("⛔ Inventory Turnover Rate: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ ITR not calculated.")
            else:
                self.fundamentals['inventoryTurnoverHistory'] = ([self.y3, self.y2, self.y1, self.y0], [inv_turnover_y3, inv_turnover_y2, inv_turnover_y1, inv_turnover_y0])
                if (inv_turnover_y0 < inv_turnover_y1 or inv_turnover_y1 < inv_turnover_y2 or inv_turnover_y2 < inv_turnover_y3) and inv_turnover_y0 > inv_turnover_y3:
                    w.append(Score.w_ITR)
                    p.append(Score.w_ITR * Score.pf_mod)
                    return Markup("⛔ Inventory Turnover Rate not consistently increasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(inv_turnover_y3) + ', ' + str(inv_turnover_y2) + ', ' + str(inv_turnover_y1) + ', ' + str(inv_turnover_y0) + "<br>\t\t\t\t\t\t<span class='text-success'>↳ although: ITR " + str(self.y3) + ' < ' + str(self.y0) + ' (' + str(inv_turnover_y3) + ' < ' + str(inv_turnover_y0) + ')')
                elif inv_turnover_y0 < inv_turnover_y1 or inv_turnover_y1 < inv_turnover_y2 or inv_turnover_y2 < inv_turnover_y3:
                    w.append(Score.w_ITR)
                    p.append(Score.w_ITR * Score.pf_neg)
                    return Markup("⛔ Inventory Turnover Rate not consistently increasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(inv_turnover_y3) + ', ' + str(inv_turnover_y2) + ', ' + str(inv_turnover_y1) + ', ' + str(inv_turnover_y0))
                elif inv_turnover_y0 >= inv_turnover_y1 and inv_turnover_y1 >= inv_turnover_y2 and (inv_turnover_y2 >= inv_turnover_y3):
                    w.append(Score.w_ITR)
                    p.append(Score.w_ITR * Score.pf_pos)
                    return Markup("✅ Inventory Turnover Rate consistently increasing!<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(inv_turnover_y3) + ', ' + str(inv_turnover_y2) + ', ' + str(inv_turnover_y1) + ', ' + str(inv_turnover_y0))
        except:
            w.append(Score.w_ITR)
            p.append(Score.w_ITR * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Inventory Turnover Rate!")

    def daysReceivablesOutstandingHistory(self):
        """ Days Receivables Outstanding (DRO) = (365*Avg.AR)/Revenue: as low as possible = fast collection of money: Consistently low or decreasing (depends on industry!)
			NB: <span class='text-info'>No data about net receivables 6y ago!  """
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            net_receivables_y0 = self._cell(bs_t, 'Net Receivables', 0)
            net_receivables_y1 = self._cell(bs_t, 'Net Receivables', 1)
            net_receivables_y2 = self._cell(bs_t, 'Net Receivables', 2)
            net_receivables_y3 = self._cell(bs_t, 'Net Receivables', 3)
            total_revenue_y0 = self._cell(pal_t, 'Total Revenue', 0)
            total_revenue_y1 = self._cell(pal_t, 'Total Revenue', 1)
            total_revenue_y2 = self._cell(pal_t, 'Total Revenue', 2)
            total_revenue_y3 = self._cell(pal_t, 'Total Revenue', 3)
            days_receivables_outstanding_y0 = round(strict_divide(365 * strict_divide(net_receivables_y0 + net_receivables_y1, 2), total_revenue_y0), 2)
            days_receivables_outstanding_y1 = round(strict_divide(365 * strict_divide(net_receivables_y1 + net_receivables_y2, 2), total_revenue_y1), 2)
            days_receivables_outstanding_y2 = round(strict_divide(365 * strict_divide(net_receivables_y2 + net_receivables_y3, 2), total_revenue_y2), 2)
            days_receivables_outstanding_y3 = round(strict_divide(365 * net_receivables_y3, total_revenue_y3), 2)
            if total_revenue_y0 <= 0 or total_revenue_y1 <= 0 or total_revenue_y2 <= 0 or (total_revenue_y3 <= 0):
                self.fundamentals['daysReceivablesOutstandingHistory'] = ([], [])
                w.append(Score.w_DRO)
                p.append(Score.w_DRO * Score.pf_mod)
                return Markup("⛔ Days Receivables Outstanding: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ DRO not calculated.")
            else:
                self.fundamentals['daysReceivablesOutstandingHistory'] = ([self.y3, self.y2, self.y1, self.y0], [days_receivables_outstanding_y3, days_receivables_outstanding_y2, days_receivables_outstanding_y1, days_receivables_outstanding_y0])
                if (days_receivables_outstanding_y0 > days_receivables_outstanding_y1 or days_receivables_outstanding_y1 > days_receivables_outstanding_y2 or days_receivables_outstanding_y2 > days_receivables_outstanding_y3) and days_receivables_outstanding_y0 < days_receivables_outstanding_y3:
                    w.append(Score.w_DRO)
                    p.append(Score.w_DRO * Score.pf_mod)
                    return Markup("⛔ Days Receivables Outstanding not consistently decreasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(days_receivables_outstanding_y3) + ' days, ' + str(days_receivables_outstanding_y2) + ' days, ' + str(days_receivables_outstanding_y1) + ' days, ' + str(days_receivables_outstanding_y0) + " days<br>\t\t\t\t\t\t<span class='text-success'>↳ although: DRO " + str(self.y3) + ' > ' + str(self.y0) + ' (' + str(days_receivables_outstanding_y3) + ' > ' + str(days_receivables_outstanding_y0) + ' days)')
                elif days_receivables_outstanding_y0 > days_receivables_outstanding_y1 or days_receivables_outstanding_y1 > days_receivables_outstanding_y2 or days_receivables_outstanding_y2 > days_receivables_outstanding_y3:
                    w.append(Score.w_DRO)
                    p.append(Score.w_DRO * Score.pf_neg)
                    return Markup("⛔ Days Receivables Outstanding not consistently decreasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(days_receivables_outstanding_y3) + ' days, ' + str(days_receivables_outstanding_y2) + ' days, ' + str(days_receivables_outstanding_y1) + ' days, ' + str(days_receivables_outstanding_y0) + ' days')
                elif days_receivables_outstanding_y0 <= days_receivables_outstanding_y1 and days_receivables_outstanding_y1 <= days_receivables_outstanding_y2 and (days_receivables_outstanding_y2 <= days_receivables_outstanding_y3):
                    w.append(Score.w_DRO)
                    p.append(Score.w_DRO * Score.pf_pos)
                    return Markup("✅ Days Receivables Outstanding consistently decreasing!<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(days_receivables_outstanding_y3) + ' days, ' + str(days_receivables_outstanding_y2) + ' days, ' + str(days_receivables_outstanding_y1) + ' days, ' + str(days_receivables_outstanding_y0) + ' days')
        except:
            w.append(Score.w_DRO)
            p.append(Score.w_DRO * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Days Receivables Outstanding!")

    def receivablesTurnoverHistory(self):
        """ Account Receivables Turnover Rate (ARTR) = Revenue/Avg. AR: as high as possible """
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            net_receivables_y0 = self._cell(bs_t, 'Net Receivables', 0)
            net_receivables_y1 = self._cell(bs_t, 'Net Receivables', 1)
            net_receivables_y2 = self._cell(bs_t, 'Net Receivables', 2)
            net_receivables_y3 = self._cell(bs_t, 'Net Receivables', 3)
            total_revenue_y0 = self._cell(pal_t, 'Total Revenue', 0)
            total_revenue_y1 = self._cell(pal_t, 'Total Revenue', 1)
            total_revenue_y2 = self._cell(pal_t, 'Total Revenue', 2)
            total_revenue_y3 = self._cell(pal_t, 'Total Revenue', 3)
            days_receivables_outstanding_y0 = round(strict_divide(365 * strict_divide(net_receivables_y0 + net_receivables_y1, 2), total_revenue_y0), 2)
            days_receivables_outstanding_y1 = round(strict_divide(365 * strict_divide(net_receivables_y1 + net_receivables_y2, 2), total_revenue_y1), 2)
            days_receivables_outstanding_y2 = round(strict_divide(365 * strict_divide(net_receivables_y2 + net_receivables_y3, 2), total_revenue_y2), 2)
            days_receivables_outstanding_y3 = round(strict_divide(365 * net_receivables_y3, total_revenue_y3), 2)
            receivables_turnover_y0 = round(strict_divide(365, days_receivables_outstanding_y0), 2)
            receivables_turnover_y1 = round(strict_divide(365, days_receivables_outstanding_y1), 2)
            receivables_turnover_y2 = round(strict_divide(365, days_receivables_outstanding_y2), 2)
            receivables_turnover_y3 = round(strict_divide(365, days_receivables_outstanding_y3), 2)
            if total_revenue_y0 <= 0 or total_revenue_y1 <= 0 or total_revenue_y2 <= 0 or (total_revenue_y3 <= 0):
                self.fundamentals['receivablesTurnoverHistory'] = ([], [])
                w.append(Score.w_ARTR)
                p.append(Score.w_ARTR * Score.pf_mod)
                return Markup("⛔ Account Receivables Turnover Rate: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ ARTR not calculated.")
            else:
                self.fundamentals['receivablesTurnoverHistory'] = ([self.y3, self.y2, self.y1, self.y0], [receivables_turnover_y3, receivables_turnover_y2, receivables_turnover_y1, receivables_turnover_y0])
                if (receivables_turnover_y0 < receivables_turnover_y1 or receivables_turnover_y1 < receivables_turnover_y2 or receivables_turnover_y2 < receivables_turnover_y3) and receivables_turnover_y0 > receivables_turnover_y3:
                    w.append(Score.w_ARTR)
                    p.append(Score.w_ARTR * Score.pf_mod)
                    return Markup("⛔ Account Receivables Turnover Rate not consistently increasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(receivables_turnover_y3) + ', ' + str(receivables_turnover_y2) + ', ' + str(receivables_turnover_y1) + ', ' + str(receivables_turnover_y0) + "<br>\t\t\t\t\t\t<span class='text-success'>↳ although: ARTR " + str(self.y3) + ' < ' + str(self.y0) + ' (' + str(receivables_turnover_y3) + ' < ' + str(receivables_turnover_y0) + ')')
                elif receivables_turnover_y0 < receivables_turnover_y1 or receivables_turnover_y1 < receivables_turnover_y2 or receivables_turnover_y2 < receivables_turnover_y3:
                    w.append(Score.w_ARTR)
                    p.append(Score.w_ARTR * Score.pf_neg)
                    return Markup("⛔ Account Receivables Turnover Rate not consistently increasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(receivables_turnover_y3) + ', ' + str(receivables_turnover_y2) + ', ' + str(receivables_turnover_y1) + ', ' + str(receivables_turnover_y0))
                elif receivables_turnover_y0 >= receivables_turnover_y1 and receivables_turnover_y1 >= receivables_turnover_y2 and (receivables_turnover_y2 >= receivables_turnover_y3):
                    w.append(Score.w_ARTR)
                    p.append(Score.w_ARTR * Score.pf_pos)
                    return Markup("✅ Account Receivables Turnover Rate consistently increasing!<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(receivables_turnover_y3) + ', ' + str(receivables_turnover_y2) + ', ' + str(receivables_turnover_y1) + ', ' + str(receivables_turnover_y0))
        except:
            w.append(Score.w_ARTR)
            p.append(Score.w_ARTR * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Account Receivables Turnover Rate!")

    def daysPayablesOutstandingHistory(self):
        """ Days Payables Outstanding (DPO) = (365*Avg.AP)/COGS: as high as possible = slow repayment of (interest free!) debt to suppliers: Consistently high or increasing (depends on industry!)
			NB:👉 <span class='text-info'>No data about account payables 6y ago! """
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            accounts_payables_y0 = self._cell(bs_t, 'Accounts Payable', 0)
            accounts_payables_y1 = self._cell(bs_t, 'Accounts Payable', 1)
            accounts_payables_y2 = self._cell(bs_t, 'Accounts Payable', 2)
            accounts_payables_y3 = self._cell(bs_t, 'Accounts Payable', 3)
            cogs_y0 = self._cell(pal_t, 'Cost Of Revenue', 0)
            cogs_y1 = self._cell(pal_t, 'Cost Of Revenue', 1)
            cogs_y2 = self._cell(pal_t, 'Cost Of Revenue', 2)
            cogs_y3 = self._cell(pal_t, 'Cost Of Revenue', 3)
            days_payables_outstanding_y0 = round(strict_divide(365 * strict_divide(accounts_payables_y0 + accounts_payables_y1, 2), cogs_y0), 2)
            days_payables_outstanding_y1 = round(strict_divide(365 * strict_divide(accounts_payables_y1 + accounts_payables_y2, 2), cogs_y1), 2)
            days_payables_outstanding_y2 = round(strict_divide(365 * strict_divide(accounts_payables_y2 + accounts_payables_y3, 2), cogs_y2), 2)
            days_payables_outstanding_y3 = round(strict_divide(365 * accounts_payables_y3, cogs_y3), 2)
            if cogs_y0 <= 0 or cogs_y1 <= 0 or cogs_y2 <= 0 or (cogs_y3 <= 0):
                self.fundamentals['daysPayablesOutstandingHistory'] = ([], [])
                w.append(Score.w_DPO)
                p.append(Score.w_DPO * Score.pf_mod)
                return Markup("⛔ Days Payables Outstanding: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ DPO not calculated.")
            else:
                self.fundamentals['daysPayablesOutstandingHistory'] = ([self.y3, self.y2, self.y1, self.y0], [days_payables_outstanding_y3, days_payables_outstanding_y2, days_payables_outstanding_y1, days_payables_outstanding_y0])
                ' CAVE liquidity problems! '
                dpo_list = [days_payables_outstanding_y0, days_payables_outstanding_y1, days_payables_outstanding_y2, days_payables_outstanding_y3]
                dpo_max = max(dpo_list)
                dpo_triggered_mean = strict_divide(sum(dpo_list) - dpo_max, len(dpo_list) - 1)
                dpo_cave = dpo_triggered_mean * (1 + 0.5)
                if (days_payables_outstanding_y0 < days_payables_outstanding_y1 or days_payables_outstanding_y1 < days_payables_outstanding_y2 or days_payables_outstanding_y2 < days_payables_outstanding_y3) and days_payables_outstanding_y0 > days_payables_outstanding_y3:
                    w.append(Score.w_DPO)
                    p.append(Score.w_DPO * Score.pf_mod)
                    return Markup("⛔ Days Payables Outstanding not consistently increasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(days_payables_outstanding_y3) + ' days, ' + str(days_payables_outstanding_y2) + ' days, ' + str(days_payables_outstanding_y1) + ' days, ' + str(days_payables_outstanding_y0) + " days<br>\t\t\t\t\t\t<span class='text-success'>↳ although: DPO " + str(self.y3) + ' < ' + str(self.y0) + ' (' + str(days_payables_outstanding_y3) + ' < ' + str(days_payables_outstanding_y0) + ' days)')
                elif (days_payables_outstanding_y0 < days_payables_outstanding_y1 or days_payables_outstanding_y1 < days_payables_outstanding_y2 or days_payables_outstanding_y2 < days_payables_outstanding_y3) and (days_payables_outstanding_y0 > dpo_cave or days_payables_outstanding_y1 > dpo_cave or days_payables_outstanding_y2 > dpo_cave or (days_payables_outstanding_y3 > dpo_cave)):
                    w.append(Score.w_DPO)
                    p.append(Score.w_DPO * Score.pf_neg)
                    return Markup("⛔ Days Payables Outstanding not consistently increasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(days_payables_outstanding_y3) + ' days, ' + str(days_payables_outstanding_y2) + ' days, ' + str(days_payables_outstanding_y1) + ' days, ' + str(days_payables_outstanding_y0) + " days<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: Aberrant DPO value! => liquidity problems?")
                elif days_payables_outstanding_y0 < days_payables_outstanding_y1 or days_payables_outstanding_y1 < days_payables_outstanding_y2 or days_payables_outstanding_y2 < days_payables_outstanding_y3:
                    w.append(Score.w_DPO)
                    p.append(Score.w_DPO * Score.pf_neg)
                    return Markup("⛔ Days Payables Outstanding not consistently increasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(days_payables_outstanding_y3) + ' days, ' + str(days_payables_outstanding_y2) + ' days, ' + str(days_payables_outstanding_y1) + ' days, ' + str(days_payables_outstanding_y0) + ' days')
                elif days_payables_outstanding_y0 >= days_payables_outstanding_y1 and days_payables_outstanding_y1 >= days_payables_outstanding_y2 and (days_payables_outstanding_y2 >= days_payables_outstanding_y3):
                    w.append(Score.w_DPO)
                    p.append(Score.w_DPO * Score.pf_pos)
                    return Markup("✅ Days Payables Outstanding consistently increasing!<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(days_payables_outstanding_y3) + ' days, ' + str(days_payables_outstanding_y2) + ' days, ' + str(days_payables_outstanding_y1) + ' days, ' + str(days_payables_outstanding_y0) + ' days')
        except:
            w.append(Score.w_DPO)
            p.append(Score.w_DPO * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Days Payables Outstanding!")

    def payablesTurnoverHistory(self):
        """ Account Payables Turnover Rate (APTR) = Revenue/Avg. AP: as low as possible """
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            accounts_payables_y0 = self._cell(bs_t, 'Accounts Payable', 0)
            accounts_payables_y1 = self._cell(bs_t, 'Accounts Payable', 1)
            accounts_payables_y2 = self._cell(bs_t, 'Accounts Payable', 2)
            accounts_payables_y3 = self._cell(bs_t, 'Accounts Payable', 3)
            cogs_y0 = self._cell(pal_t, 'Cost Of Revenue', 0)
            cogs_y1 = self._cell(pal_t, 'Cost Of Revenue', 1)
            cogs_y2 = self._cell(pal_t, 'Cost Of Revenue', 2)
            cogs_y3 = self._cell(pal_t, 'Cost Of Revenue', 3)
            days_payables_outstanding_y0 = round(strict_divide(365 * strict_divide(accounts_payables_y0 + accounts_payables_y1, 2), cogs_y0), 2)
            days_payables_outstanding_y1 = round(strict_divide(365 * strict_divide(accounts_payables_y1 + accounts_payables_y2, 2), cogs_y1), 2)
            days_payables_outstanding_y2 = round(strict_divide(365 * strict_divide(accounts_payables_y2 + accounts_payables_y3, 2), cogs_y2), 2)
            days_payables_outstanding_y3 = round(strict_divide(365 * accounts_payables_y3, cogs_y3), 2)
            payables_turnover_y0 = round(strict_divide(365, days_payables_outstanding_y0), 2)
            payables_turnover_y1 = round(strict_divide(365, days_payables_outstanding_y1), 2)
            payables_turnover_y2 = round(strict_divide(365, days_payables_outstanding_y2), 2)
            payables_turnover_y3 = round(strict_divide(365, days_payables_outstanding_y3), 2)
            if cogs_y0 <= 0 or cogs_y1 <= 0 or cogs_y2 <= 0 or (cogs_y3 <= 0):
                self.fundamentals['payablesTurnoverHistory'] = ([], [])
                w.append(Score.w_APTR)
                p.append(Score.w_APTR * Score.pf_mod)
                return Markup("⛔ Account Payables Turnover Rate: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ APTR not calculated.")
            else:
                self.fundamentals['payablesTurnoverHistory'] = ([self.y3, self.y2, self.y1, self.y0], [payables_turnover_y3, payables_turnover_y2, payables_turnover_y1, payables_turnover_y0])
                if payables_turnover_y0 > payables_turnover_y1 or payables_turnover_y1 > payables_turnover_y2 or payables_turnover_y2 > payables_turnover_y3:
                    w.append(Score.w_APTR)
                    p.append(Score.w_APTR * Score.pf_neg)
                    return Markup("⛔ Account Payables Turnover Rate not consistently decreasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(payables_turnover_y3) + ', ' + str(payables_turnover_y2) + ', ' + str(payables_turnover_y1) + ', ' + str(payables_turnover_y0))
                elif (payables_turnover_y0 > payables_turnover_y1 or payables_turnover_y1 > payables_turnover_y2 or payables_turnover_y2 > payables_turnover_y3) and payables_turnover_y0 < payables_turnover_y3:
                    w.append(Score.w_APTR)
                    p.append(Score.w_APTR * Score.pf_mod)
                    return Markup("⛔ Account Payables Turnover Rate not consistently decreasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(payables_turnover_y3) + ', ' + str(payables_turnover_y2) + ', ' + str(payables_turnover_y1) + ', ' + str(payables_turnover_y0) + "<br>\t\t\t\t\t\t<span class='text-success'>↳ although: APTR " + str(self.y3) + ' > ' + str(self.y0) + ' (' + str(payables_turnover_y3) + ' > ' + str(payables_turnover_y0) + ')')
                elif payables_turnover_y0 <= payables_turnover_y1 and payables_turnover_y1 <= payables_turnover_y2 and (payables_turnover_y2 <= payables_turnover_y3):
                    w.append(Score.w_APTR)
                    p.append(Score.w_APTR * Score.pf_pos)
                    return Markup("✅ Account Payables Turnover Rate consistently decreasing!<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(payables_turnover_y3) + ', ' + str(payables_turnover_y2) + ', ' + str(payables_turnover_y1) + ', ' + str(payables_turnover_y0))
        except:
            w.append(Score.w_APTR)
            p.append(Score.w_APTR * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Account Receivables Turnover Rate!")

    def cashConversionCycleHistory(self):
        """ Cash Conversion Cycle: consistently low = money supply to do business is high """
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            inv_y0 = self._cell(bs_t, 'Inventory', 0)
            inv_y1 = self._cell(bs_t, 'Inventory', 1)
            inv_y2 = self._cell(bs_t, 'Inventory', 2)
            inv_y3 = self._cell(bs_t, 'Inventory', 3)
            net_receivables_y0 = self._cell(bs_t, 'Net Receivables', 0)
            net_receivables_y1 = self._cell(bs_t, 'Net Receivables', 1)
            net_receivables_y2 = self._cell(bs_t, 'Net Receivables', 2)
            net_receivables_y3 = self._cell(bs_t, 'Net Receivables', 3)
            accounts_payables_y0 = self._cell(bs_t, 'Accounts Payable', 0)
            accounts_payables_y1 = self._cell(bs_t, 'Accounts Payable', 1)
            accounts_payables_y2 = self._cell(bs_t, 'Accounts Payable', 2)
            accounts_payables_y3 = self._cell(bs_t, 'Accounts Payable', 3)
            cogs_y0 = self._cell(pal_t, 'Cost Of Revenue', 0)
            cogs_y1 = self._cell(pal_t, 'Cost Of Revenue', 1)
            cogs_y2 = self._cell(pal_t, 'Cost Of Revenue', 2)
            cogs_y3 = self._cell(pal_t, 'Cost Of Revenue', 3)
            total_revenue_y0 = self._cell(pal_t, 'Total Revenue', 0)
            total_revenue_y1 = self._cell(pal_t, 'Total Revenue', 1)
            total_revenue_y2 = self._cell(pal_t, 'Total Revenue', 2)
            total_revenue_y3 = self._cell(pal_t, 'Total Revenue', 3)
            days_inv_on_hand_y0 = round(strict_divide(365 * strict_divide(inv_y0 + inv_y1, 2), cogs_y0), 2)
            days_inv_on_hand_y1 = round(strict_divide(365 * strict_divide(inv_y1 + inv_y2, 2), cogs_y1), 2)
            days_inv_on_hand_y2 = round(strict_divide(365 * strict_divide(inv_y2 + inv_y3, 2), cogs_y2), 2)
            days_inv_on_hand_y3 = round(strict_divide(365 * inv_y3, cogs_y3), 2)
            days_receivables_outstanding_y0 = round(strict_divide(365 * strict_divide(net_receivables_y0 + net_receivables_y1, 2), total_revenue_y0), 2)
            days_receivables_outstanding_y1 = round(strict_divide(365 * strict_divide(net_receivables_y1 + net_receivables_y2, 2), total_revenue_y1), 2)
            days_receivables_outstanding_y2 = round(strict_divide(365 * strict_divide(net_receivables_y2 + net_receivables_y3, 2), total_revenue_y2), 2)
            days_receivables_outstanding_y3 = round(strict_divide(365 * net_receivables_y3, total_revenue_y3), 2)
            days_payables_outstanding_y0 = round(strict_divide(365 * strict_divide(accounts_payables_y0 + accounts_payables_y1, 2), cogs_y0), 2)
            days_payables_outstanding_y1 = round(strict_divide(365 * strict_divide(accounts_payables_y1 + accounts_payables_y2, 2), cogs_y1), 2)
            days_payables_outstanding_y2 = round(strict_divide(365 * strict_divide(accounts_payables_y2 + accounts_payables_y3, 2), cogs_y2), 2)
            days_payables_outstanding_y3 = round(strict_divide(365 * accounts_payables_y3, cogs_y3), 2)
            cash_conversion_cycle_y0 = round(days_inv_on_hand_y0 + days_receivables_outstanding_y0 - days_payables_outstanding_y0, 2)
            cash_conversion_cycle_y1 = round(days_inv_on_hand_y1 + days_receivables_outstanding_y1 - days_payables_outstanding_y1, 2)
            cash_conversion_cycle_y2 = round(days_inv_on_hand_y2 + days_receivables_outstanding_y2 - days_payables_outstanding_y2, 2)
            cash_conversion_cycle_y3 = round(days_inv_on_hand_y3 + days_receivables_outstanding_y3 - days_payables_outstanding_y3, 2)
            if cogs_y0 <= 0 or cogs_y1 <= 0 or cogs_y2 <= 0 or (cogs_y3 <= 0) or (total_revenue_y0 <= 0) or (total_revenue_y1 <= 0) or (total_revenue_y2 <= 0) or (total_revenue_y3 <= 0):
                self.fundamentals['cashConversionCycleHistory'] = ([], [])
                w.append(Score.w_CCC)
                p.append(Score.w_CCC * Score.pf_mod)
                return Markup("⛔ Cash Conversion Cycle: COGS or Total Revenue ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ CCC not calculated.")
            else:
                self.fundamentals['cashConversionCycleHistory'] = ([self.y3, self.y2, self.y1, self.y0], [cash_conversion_cycle_y3, cash_conversion_cycle_y2, cash_conversion_cycle_y1, cash_conversion_cycle_y0])
                if cash_conversion_cycle_y0 < 0 and cash_conversion_cycle_y1 < 0 and (cash_conversion_cycle_y2 < 0) and (cash_conversion_cycle_y3 < 0):
                    w.append(Score.w_CCC_all_negative)
                    p.append(Score.w_CCC_all_negative * Score.pf_pos)
                    return Markup("✅ Cash Conversion Cycle all NEGATIVE!<br>\t\t\t\t\t\t<span class='text-success'>↳ CCC " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cash_conversion_cycle_y3) + ' days, ' + str(cash_conversion_cycle_y2) + ' days, ' + str(cash_conversion_cycle_y1) + ' days, ' + str(cash_conversion_cycle_y0) + " days<br>\t\t\t\t\t\t<span class='text-success'>↳ Business operations financed by suppliers!")
                elif ((cash_conversion_cycle_y0 > 0 or cash_conversion_cycle_y1 > 0 or cash_conversion_cycle_y2 > 0 or (cash_conversion_cycle_y3 > 0)) and (cash_conversion_cycle_y0 > cash_conversion_cycle_y1 or cash_conversion_cycle_y1 > cash_conversion_cycle_y2 or cash_conversion_cycle_y2 > cash_conversion_cycle_y3)) and cash_conversion_cycle_y0 < cash_conversion_cycle_y3:
                    w.append(Score.w_CCC)
                    p.append(Score.w_CCC * Score.pf_mod)
                    return Markup("⛔ Cash Conversion Cycle not consistently decreasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ CCC " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cash_conversion_cycle_y3) + ' days, ' + str(cash_conversion_cycle_y2) + ' days, ' + str(cash_conversion_cycle_y1) + ' days, ' + str(cash_conversion_cycle_y0) + " days<br>\t\t\t\t\t\t<span class='text-success'>↳ although: CCC " + str(self.y3) + ' > ' + str(self.y0) + ' (' + str(cash_conversion_cycle_y3) + ' > ' + str(cash_conversion_cycle_y0) + ' days)')
                elif (cash_conversion_cycle_y0 > 0 or cash_conversion_cycle_y1 > 0 or cash_conversion_cycle_y2 > 0 or (cash_conversion_cycle_y3 > 0)) and (cash_conversion_cycle_y0 > cash_conversion_cycle_y1 or cash_conversion_cycle_y1 > cash_conversion_cycle_y2 or cash_conversion_cycle_y2 > cash_conversion_cycle_y3):
                    w.append(Score.w_CCC)
                    p.append(Score.w_CCC * Score.pf_neg)
                    return Markup("⛔ Cash Conversion Cycle not consistently decreasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ CCC " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cash_conversion_cycle_y3) + ' days, ' + str(cash_conversion_cycle_y2) + ' days, ' + str(cash_conversion_cycle_y1) + ' days, ' + str(cash_conversion_cycle_y0) + ' days')
                elif cash_conversion_cycle_y0 <= cash_conversion_cycle_y1 and cash_conversion_cycle_y1 <= cash_conversion_cycle_y2 and (cash_conversion_cycle_y2 <= cash_conversion_cycle_y3):
                    w.append(Score.w_CCC)
                    p.append(Score.w_CCC * Score.pf_pos)
                    return Markup("✅ Cash Conversion Cycle consistently decreasing!<br>\t\t\t\t\t\t<span class='text-success'>↳ CCC " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cash_conversion_cycle_y3) + ' days, ' + str(cash_conversion_cycle_y2) + ' days, ' + str(cash_conversion_cycle_y1) + ' days, ' + str(cash_conversion_cycle_y0) + ' days')
        except:
            w.append(Score.w_CCC)
            p.append(Score.w_CCC * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Cash Conversion Cycle!")

    def grossProfitMarginHistory(self):
        """ GPM = Gross profit/sales(revenue) ≥ 40% (COGS minimal) """
        data = self.data
        pal_t = self.pal_t
        w = self.weights_list
        p = self.points_list
        try:
            gross_profit_y0 = self._cell(pal_t, 'Gross Profit', 0)
            gross_profit_y1 = self._cell(pal_t, 'Gross Profit', 1)
            gross_profit_y2 = self._cell(pal_t, 'Gross Profit', 2)
            gross_profit_y3 = self._cell(pal_t, 'Gross Profit', 3)
            total_revenue_y0 = self._cell(pal_t, 'Total Revenue', 0)
            total_revenue_y1 = self._cell(pal_t, 'Total Revenue', 1)
            total_revenue_y2 = self._cell(pal_t, 'Total Revenue', 2)
            total_revenue_y3 = self._cell(pal_t, 'Total Revenue', 3)
            gross_profit_margin_y0 = round(strict_divide(gross_profit_y0, total_revenue_y0) * 100, 2)
            gross_profit_margin_y1 = round(strict_divide(gross_profit_y1, total_revenue_y1) * 100, 2)
            gross_profit_margin_y2 = round(strict_divide(gross_profit_y2, total_revenue_y2) * 100, 2)
            gross_profit_margin_y3 = round(strict_divide(gross_profit_y3, total_revenue_y3) * 100, 2)
            if total_revenue_y0 <= 0 or total_revenue_y1 <= 0 or total_revenue_y2 <= 0 or (total_revenue_y3 <= 0):
                self.fundamentals['grossProfitMarginHistory'] = ([], [])
                w.append(Score.w_GPM)
                p.append(Score.w_GPM * Score.pf_mod)
                return Markup("⛔ Gross Profit Margin: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ GPM not calculated.")
            else:
                self.fundamentals['grossProfitMarginHistory'] = ([self.y3, self.y2, self.y1, self.y0], [gross_profit_margin_y3, gross_profit_margin_y2, gross_profit_margin_y1, gross_profit_margin_y0])
                if (gross_profit_margin_y0 < 40 or gross_profit_margin_y1 < 40 or gross_profit_margin_y2 < 40 or (gross_profit_margin_y3 < 40)) and (gross_profit_margin_y0 > gross_profit_margin_y1 and gross_profit_margin_y1 > gross_profit_margin_y2 and (gross_profit_margin_y2 > gross_profit_margin_y3)):
                    w.append(Score.w_GPM)
                    p.append(Score.w_GPM * Score.pf_mod)
                    w.append(Score.w_GPM_increasing)
                    p.append(Score.w_GPM_increasing * Score.pf_pos)
                    return Markup("⛔ GPM < 40%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(gross_profit_margin_y3) + '%, ' + str(gross_profit_margin_y2) + '%, ' + str(gross_profit_margin_y1) + '%, ' + str(gross_profit_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: GPM consistently increasing")
                elif (gross_profit_margin_y0 < 40 or gross_profit_margin_y1 < 40 or gross_profit_margin_y2 < 40 or (gross_profit_margin_y3 < 40)) and gross_profit_margin_y0 >= 40:
                    w.append(Score.w_GPM)
                    p.append(Score.w_GPM * Score.pf_mod)
                    return Markup("⛔ GPM < 40%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(gross_profit_margin_y3) + '%, ' + str(gross_profit_margin_y2) + '%, ' + str(gross_profit_margin_y1) + '%, ' + str(gross_profit_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: GPM " + str(self.y0) + ' ≥ 40% (' + str(gross_profit_margin_y0) + '%)')
                elif gross_profit_margin_y0 < 40 or gross_profit_margin_y1 < 40 or gross_profit_margin_y2 < 40 or (gross_profit_margin_y3 < 40):
                    w.append(Score.w_GPM)
                    p.append(Score.w_GPM * Score.pf_neg)
                    return Markup("⛔ GPM < 40%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(gross_profit_margin_y3) + '%, ' + str(gross_profit_margin_y2) + '%, ' + str(gross_profit_margin_y1) + '%, ' + str(gross_profit_margin_y0) + '%')
                elif (gross_profit_margin_y0 >= 40 and gross_profit_margin_y1 >= 40 and (gross_profit_margin_y2 >= 40) and (gross_profit_margin_y3 >= 40)) and (gross_profit_margin_y0 < gross_profit_margin_y1 and gross_profit_margin_y1 < gross_profit_margin_y2 and (gross_profit_margin_y2 < gross_profit_margin_y3)):
                    w.append(Score.w_GPM)
                    p.append(Score.w_GPM * Score.pf_pos)
                    w.append(Score.w_GPM_decreasing)
                    p.append(Score.w_GPM_decreasing * Score.pf_neg)
                    return Markup("✅ GPM ≥ 40%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(gross_profit_margin_y3) + '%, ' + str(gross_profit_margin_y2) + '%, ' + str(gross_profit_margin_y1) + '%, ' + str(gross_profit_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: GPM consistently decreasing")
                elif gross_profit_margin_y0 >= 40 and gross_profit_margin_y1 >= 40 and (gross_profit_margin_y2 >= 40) and (gross_profit_margin_y3 >= 40):
                    w.append(Score.w_GPM)
                    p.append(Score.w_GPM * Score.pf_pos)
                    return Markup("✅ GPM ≥ 40%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(gross_profit_margin_y3) + '%, ' + str(gross_profit_margin_y2) + '%, ' + str(gross_profit_margin_y1) + '%, ' + str(gross_profit_margin_y0) + '%')
        except:
            w.append(Score.w_GPM)
            p.append(Score.w_GPM * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about GPM!")

    def netProfitMarginHistory(self):
        """ NPM = Net income/total revenue >= 20% (never invest if <10%) """
        data = self.data
        pal_t = self.pal_t
        w = self.weights_list
        p = self.points_list
        try:
            net_income_y0 = self._cell(pal_t, 'Net Income', 0)
            net_income_y1 = self._cell(pal_t, 'Net Income', 1)
            net_income_y2 = self._cell(pal_t, 'Net Income', 2)
            net_income_y3 = self._cell(pal_t, 'Net Income', 3)
            total_revenue_y0 = self._cell(pal_t, 'Total Revenue', 0)
            total_revenue_y1 = self._cell(pal_t, 'Total Revenue', 1)
            total_revenue_y2 = self._cell(pal_t, 'Total Revenue', 2)
            total_revenue_y3 = self._cell(pal_t, 'Total Revenue', 3)
            profit_margin_y0 = round(strict_divide(net_income_y0, total_revenue_y0) * 100, 2)
            profit_margin_y1 = round(strict_divide(net_income_y1, total_revenue_y1) * 100, 2)
            profit_margin_y2 = round(strict_divide(net_income_y2, total_revenue_y2) * 100, 2)
            profit_margin_y3 = round(strict_divide(net_income_y3, total_revenue_y3) * 100, 2)
            if total_revenue_y0 <= 0 or total_revenue_y1 <= 0 or total_revenue_y2 <= 0 or (total_revenue_y3 <= 0):
                self.fundamentals['netProfitMarginHistory'] = ([], [])
                w.append(Score.w_NPM)
                p.append(Score.w_NPM * Score.pf_mod)
                return Markup("⛔ Net Profit Margin: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ NPM not calculated.")
            else:
                self.fundamentals['netProfitMarginHistory'] = ([self.y3, self.y2, self.y1, self.y0], [profit_margin_y3, profit_margin_y2, profit_margin_y1, profit_margin_y0])
                if profit_margin_y0 < 10 or profit_margin_y1 < 10 or profit_margin_y2 < 10 or (profit_margin_y3 < 10):
                    w.append(Score.w_NPM)
                    p.append(Score.w_NPM * Score.pf_neg)
                    return Markup("⛔ NPM < 20%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(profit_margin_y3) + '%, ' + str(profit_margin_y2) + '%, ' + str(profit_margin_y1) + '%, ' + str(profit_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ NPM < 10%: Avoid to invest in these types of stocks!")
                elif (profit_margin_y0 < 20 or profit_margin_y1 < 20 or profit_margin_y2 < 20 or (profit_margin_y3 < 20)) and profit_margin_y0 < 10:
                    w.append(Score.w_NPM)
                    p.append(Score.w_NPM * Score.pf_neg)
                    return Markup("⛔ NPM < 20%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(profit_margin_y3) + '%, ' + str(profit_margin_y2) + '%, ' + str(profit_margin_y1) + '%, ' + str(profit_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: NPM " + str(self.y0) + ' < 10%: Avoid to invest in these types of stocks!')
                elif (profit_margin_y0 < 20 or profit_margin_y1 < 20 or profit_margin_y2 < 20 or (profit_margin_y3 < 20)) and (profit_margin_y0 > profit_margin_y1 and profit_margin_y1 > profit_margin_y2 and (profit_margin_y2 > profit_margin_y3)):
                    w.append(Score.w_NPM)
                    p.append(Score.w_NPM * Score.pf_mod)
                    w.append(Score.w_NPM_increasing)
                    p.append(Score.w_NPM_increasing * Score.pf_pos)
                    return Markup("⛔ NPM < 20%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(profit_margin_y3) + '%, ' + str(profit_margin_y2) + '%, ' + str(profit_margin_y1) + '%, ' + str(profit_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: NPM consistently increasing")
                elif (profit_margin_y0 < 20 or profit_margin_y1 < 20 or profit_margin_y2 < 20 or (profit_margin_y3 < 20)) and profit_margin_y0 >= 20:
                    w.append(Score.w_NPM)
                    p.append(Score.w_NPM * Score.pf_mod)
                    return Markup("⛔ NPM < 20%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(profit_margin_y3) + '%, ' + str(profit_margin_y2) + '%, ' + str(profit_margin_y1) + '%, ' + str(profit_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: NPM " + str(self.y0) + ' ≥ 20% (' + str(profit_margin_y0) + '%)')
                elif profit_margin_y0 < 20 or profit_margin_y1 < 20 or profit_margin_y2 < 20 or (profit_margin_y3 < 20):
                    w.append(Score.w_NPM)
                    p.append(Score.w_NPM * Score.pf_neg)
                    return Markup("⛔ NPM < 20%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(profit_margin_y3) + '%, ' + str(profit_margin_y2) + '%, ' + str(profit_margin_y1) + '%, ' + str(profit_margin_y0) + '%')
                elif (profit_margin_y0 >= 20 and profit_margin_y1 >= 20 and (profit_margin_y2 >= 20) and (profit_margin_y3 >= 20)) and (profit_margin_y0 < profit_margin_y1 and profit_margin_y1 < profit_margin_y2 and (profit_margin_y2 < profit_margin_y3)):
                    w.append(Score.w_NPM)
                    p.append(Score.w_NPM * Score.pf_pos)
                    w.append(Score.w_NPM_decreasing)
                    p.append(Score.w_NPM_decreasing * Score.pf_neg)
                    return Markup("✅ NPM ≥ 20%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(profit_margin_y3) + '%, ' + str(profit_margin_y2) + '%, ' + str(profit_margin_y1) + '%, ' + str(profit_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: NPM consistently decreasing")
                elif profit_margin_y0 >= 20 and profit_margin_y1 >= 20 and (profit_margin_y2 >= 20) and (profit_margin_y3 >= 20):
                    w.append(Score.w_NPM)
                    p.append(Score.w_NPM * Score.pf_pos)
                    return Markup("✅ NPM ≥ 20%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(profit_margin_y3) + '%, ' + str(profit_margin_y2) + '%, ' + str(profit_margin_y1) + '%, ' + str(profit_margin_y0) + '%')
        except:
            w.append(Score.w_NPM)
            p.append(Score.w_NPM * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Net Profit Margin!")

    def retainedEarningsHistory(self):
        """ RE: Consistent increasing Retained Earnings >7y! """
        data = self.data
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            retained_earnings_y0 = round(strict_divide(self._cell(bs_t, 'Retained Earnings', 0), 1000000), 2)
            retained_earnings_y1 = round(strict_divide(self._cell(bs_t, 'Retained Earnings', 1), 1000000), 2)
            retained_earnings_y2 = round(strict_divide(self._cell(bs_t, 'Retained Earnings', 2), 1000000), 2)
            retained_earnings_y3 = round(strict_divide(self._cell(bs_t, 'Retained Earnings', 3), 1000000), 2)
            net_income_y0 = self._cell(pal_t, 'Net Income', 0)
            net_income_y1 = self._cell(pal_t, 'Net Income', 1)
            net_income_y2 = self._cell(pal_t, 'Net Income', 2)
            net_income_y3 = self._cell(pal_t, 'Net Income', 3)
            retention_ratio_y0 = round(strict_divide(retained_earnings_y0, net_income_y0) * 100, 2)
            retention_ratio_y1 = round(strict_divide(retained_earnings_y1, net_income_y1) * 100, 2)
            retention_ratio_y2 = round(strict_divide(retained_earnings_y2, net_income_y2) * 100, 2)
            retention_ratio_y3 = round(strict_divide(retained_earnings_y3, net_income_y3) * 100, 2)
            if net_income_y0 <= 0 or net_income_y1 <= 0 or net_income_y2 <= 0 or (net_income_y3 <= 0):
                self.fundamentals['retentionRatioHistory'] = ([], [])
            else:
                self.fundamentals['retentionRatioHistory'] = ([self.y3, self.y2, self.y1, self.y0], [retention_ratio_y3, retention_ratio_y2, retention_ratio_y1, retention_ratio_y0])
                self.fundamentals['retainedEarningsHistory'] = ([self.y3, self.y2, self.y1, self.y0], [retained_earnings_y3, retained_earnings_y2, retained_earnings_y1, retained_earnings_y0])
                if (retained_earnings_y0 < retained_earnings_y1 or retained_earnings_y1 < retained_earnings_y2 or retained_earnings_y2 < retained_earnings_y3) and retained_earnings_y0 > retained_earnings_y3:
                    w.append(Score.w_RE)
                    p.append(Score.w_RE * Score.pf_mod)
                    return Markup("⛔ RE not consistently increasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(retained_earnings_y3) + ', ' + str(retained_earnings_y2) + ', ' + str(retained_earnings_y1) + ', ' + str(retained_earnings_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t\t<span class='text-success'>↳ although: RE " + str(self.y3) + ' < ' + str(self.y0) + ' (' + str(retained_earnings_y3) + ' < ' + str(retained_earnings_y0) + ' mln ' + data['currency'] + ')')
                elif retained_earnings_y0 < retained_earnings_y1 or retained_earnings_y1 < retained_earnings_y2 or retained_earnings_y2 < retained_earnings_y3:
                    w.append(Score.w_RE)
                    p.append(Score.w_RE * Score.pf_neg)
                    return Markup("⛔ RE not consistently increasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(retained_earnings_y3) + ', ' + str(retained_earnings_y2) + ', ' + str(retained_earnings_y1) + ', ' + str(retained_earnings_y0) + ' mln ' + data['currency'])
                elif retained_earnings_y0 > retained_earnings_y1 and retained_earnings_y1 > retained_earnings_y2 and (retained_earnings_y2 > retained_earnings_y3):
                    w.append(Score.w_RE)
                    p.append(Score.w_RE * Score.pf_pos)
                    return Markup("✅ RE consistently increasing!<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(retained_earnings_y3) + ', ' + str(retained_earnings_y2) + ', ' + str(retained_earnings_y1) + ', ' + str(retained_earnings_y0) + ' mln ' + data['currency'])
        except:
            w.append(Score.w_RE)
            p.append(Score.w_RE * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about consistency Retained Earnings!")

    def netEarningsTocommonHistory(self):
        """ Inventory and NI to Common: Consistent increasing inventory AND net earnings at the same time >7y!
			NB: Gains/losses remove out of valuation or projection NI! """
        data = self.data
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            inv_y0 = round(strict_divide(self._cell(bs_t, 'Inventory', 0), 1000000), 2)
            inv_y1 = round(strict_divide(self._cell(bs_t, 'Inventory', 1), 1000000), 2)
            inv_y2 = round(strict_divide(self._cell(bs_t, 'Inventory', 2), 1000000), 2)
            inv_y3 = round(strict_divide(self._cell(bs_t, 'Inventory', 3), 1000000), 2)
            net_income_tocommon_ttm = round(strict_divide(data['netIncomeToCommon'], 1000000), 2)
            net_earnings_tocommon_y0 = round(strict_divide(self._cell(pal_t, 'Net Income Applicable To Common Shares', 0), 1000000), 2)
            net_earnings_tocommon_y1 = round(strict_divide(self._cell(pal_t, 'Net Income Applicable To Common Shares', 1), 1000000), 2)
            net_earnings_tocommon_y2 = round(strict_divide(self._cell(pal_t, 'Net Income Applicable To Common Shares', 2), 1000000), 2)
            net_earnings_tocommon_y3 = round(strict_divide(self._cell(pal_t, 'Net Income Applicable To Common Shares', 3), 1000000), 2)
            self.fundamentals['netEarningsTocommonHistory'] = ([self.y3, self.y2, self.y1, self.y0], [net_earnings_tocommon_y3, net_earnings_tocommon_y2, net_earnings_tocommon_y1, net_earnings_tocommon_y0])
            self.fundamentals['inventoryHistory'] = ([self.y3, self.y2, self.y1, self.y0], [inv_y3, inv_y2, inv_y1, inv_y0])
            if ((inv_y0 < inv_y1 or inv_y1 < inv_y2 or inv_y2 < inv_y3) and (net_income_tocommon_ttm < net_earnings_tocommon_y0 or net_earnings_tocommon_y0 < net_earnings_tocommon_y1 or net_earnings_tocommon_y1 < net_earnings_tocommon_y2 or (net_earnings_tocommon_y2 < net_earnings_tocommon_y3))) and (inv_y0 > inv_y3 and net_income_tocommon_ttm > net_earnings_tocommon_y3):
                w.append(Score.w_Inv_NItC)
                p.append(Score.w_Inv_NItC * Score.pf_mod)
                return Markup("⛔ Both Inventory and NItC not consistently increasing!<br>\t\t\t\t\t<span class='text-danger'>↳ Inv. " + str(self.y3) + '-' + str(self.y0) + ': ' + str(inv_y3) + ', ' + str(inv_y2) + ', ' + str(inv_y1) + ', ' + str(inv_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ NItC " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(net_earnings_tocommon_y3) + ', ' + str(net_earnings_tocommon_y2) + ', ' + str(net_earnings_tocommon_y1) + ', ' + str(net_earnings_tocommon_y0) + ', ' + str(net_income_tocommon_ttm) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-success'>↳ although: Inventory " + str(self.y3) + ' < ' + str(self.ttm) + ' (' + str(inv_y3) + ' < ' + str(inv_y0) + ' mln ' + data['currency'] + ")<br>\t\t\t\t\t<span class='text-success'>↳ while: NItC " + str(self.y3) + ' < ' + str(self.ttm) + ' (' + str(net_earnings_tocommon_y3) + ' < ' + str(net_income_tocommon_ttm) + ' mln ' + data['currency'] + ')')
            elif (inv_y0 < inv_y1 or inv_y1 < inv_y2 or inv_y2 < inv_y3) and (net_income_tocommon_ttm < net_earnings_tocommon_y0 or net_earnings_tocommon_y0 < net_earnings_tocommon_y1 or net_earnings_tocommon_y1 < net_earnings_tocommon_y2 or (net_earnings_tocommon_y2 < net_earnings_tocommon_y3)):
                w.append(Score.w_Inv_NItC)
                p.append(Score.w_Inv_NItC * Score.pf_neg)
                return Markup("⛔ Both Inventory and NItC not consistently increasing!<br>\t\t\t\t\t<span class='text-danger'>↳ Inv. " + str(self.y3) + '-' + str(self.y0) + ': ' + str(inv_y3) + ', ' + str(inv_y2) + ', ' + str(inv_y1) + ', ' + str(inv_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ NItC " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(net_earnings_tocommon_y3) + ', ' + str(net_earnings_tocommon_y2) + ', ' + str(net_earnings_tocommon_y1) + ', ' + str(net_earnings_tocommon_y0) + ', ' + str(net_income_tocommon_ttm) + ' mln ' + data['currency'])
            elif (inv_y0 > inv_y1 and inv_y1 > inv_y2 and (inv_y2 > inv_y3)) and (net_income_tocommon_ttm > net_earnings_tocommon_y0 and net_earnings_tocommon_y0 > net_earnings_tocommon_y1 and (net_earnings_tocommon_y1 > net_earnings_tocommon_y2) and (net_earnings_tocommon_y2 > net_earnings_tocommon_y3)):
                w.append(Score.w_Inv_NItC)
                p.append(Score.w_Inv_NItC * Score.pf_pos)
                return Markup("✅ Both Inventory and NItC consistently increasing!<br>\t\t\t\t\t<span class='text-success'>↳ Inv. " + str(self.y3) + '-' + str(self.y0) + ': ' + str(inv_y3) + ', ' + str(inv_y2) + ', ' + str(inv_y1) + ', ' + str(inv_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-success'>↳ NItC " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(net_earnings_tocommon_y3) + ', ' + str(net_earnings_tocommon_y2) + ', ' + str(net_earnings_tocommon_y1) + ', ' + str(net_earnings_tocommon_y0) + ', ' + str(net_income_tocommon_ttm) + ' mln ' + data['currency'])
        except:
            w.append(Score.w_Inv_NItC)
            p.append(Score.w_Inv_NItC * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about correlation Inventory and NI to Common!")

    def earningsPerShareHistory(self):
        """ EPS: Consistent increasing EPS >7y!
			CAVE: CALCULATED ON CURRENT SO: that is disadvantageous for companies that repurchase own shares and advantageous for companies that issue stock! """
        data = self.data
        revenue_and_earnings = self.revenue_and_earnings
        w = self.weights_list
        p = self.points_list
        try:
            data_so = data['sharesOutstanding']
            net_earnings_y0 = self._cell(revenue_and_earnings, 'Earnings', 3)
            net_earnings_y1 = self._cell(revenue_and_earnings, 'Earnings', 2)
            net_earnings_y2 = self._cell(revenue_and_earnings, 'Earnings', 1)
            net_earnings_y3 = self._cell(revenue_and_earnings, 'Earnings', 0)
            eps_ttm = round(data['trailingEps'], 3)
            eps_y0 = round(strict_divide(net_earnings_y0, data_so), 3)
            eps_y1 = round(strict_divide(net_earnings_y1, data_so), 3)
            eps_y2 = round(strict_divide(net_earnings_y2, data_so), 3)
            eps_y3 = round(strict_divide(net_earnings_y3, data_so), 3)
            self.fundamentals['earningsPerShareHistory'] = ([self.y3, self.y2, self.y1, self.y0, self.ttm], [eps_y3, eps_y2, eps_y1, eps_y0, eps_ttm])
            if (eps_ttm <= eps_y0 or eps_y0 <= eps_y1 or eps_y1 <= eps_y2 or (eps_y2 <= eps_y3)) and eps_ttm > eps_y3:
                w.append(Score.w_EPS)
                p.append(Score.w_EPS * Score.pf_mod)
                return Markup("⛔ EPS not consistently increasing!<br>\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(eps_y3) + ', ' + str(eps_y2) + ', ' + str(eps_y1) + ', ' + str(eps_y0) + ', ' + str(eps_ttm) + ' ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-success'>↳ although: EPS " + str(self.y3) + ' < ' + str(self.ttm) + ' (' + str(eps_y3) + ' < ' + str(eps_ttm) + ' ' + data['currency'] + ')')
            elif eps_ttm <= eps_y0 or eps_y0 <= eps_y1 or eps_y1 <= eps_y2 or (eps_y2 <= eps_y3):
                w.append(Score.w_EPS)
                p.append(Score.w_EPS * Score.pf_neg)
                return Markup("⛔ EPS not consistently increasing!<br>\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(eps_y3) + ', ' + str(eps_y2) + ', ' + str(eps_y1) + ', ' + str(eps_y0) + ', ' + str(eps_ttm) + ' ' + data['currency'])
            elif eps_ttm > eps_y0 and eps_y0 > eps_y1 and (eps_y1 > eps_y2) and (eps_y2 > eps_y3):
                w.append(Score.w_EPS)
                p.append(Score.w_EPS * Score.pf_pos)
                return Markup("✅ EPS consistently increasing!<br>\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(eps_y3) + ', ' + str(eps_y2) + ', ' + str(eps_y1) + ', ' + str(eps_y0) + ', ' + str(eps_ttm) + ' ' + data['currency'])
        except:
            w.append(Score.w_EPS)
            p.append(Score.w_EPS * Score.pf_mod)
            return Markup("❓ <span class='text-info'><span class='text-info'>No data about consistency EPS!")

    def sellingGeneralAdministrativeMarginHistory(self):
        """ SGA Margin = SGA/gross profit < 30% """
        pal_t = self.pal_t
        w = self.weights_list
        p = self.points_list
        try:
            sga_y0 = self._cell(pal_t, 'Selling General Administrative', 0)
            sga_y1 = self._cell(pal_t, 'Selling General Administrative', 1)
            sga_y2 = self._cell(pal_t, 'Selling General Administrative', 2)
            sga_y3 = self._cell(pal_t, 'Selling General Administrative', 3)
            gross_profit_y0 = self._cell(pal_t, 'Gross Profit', 0)
            gross_profit_y1 = self._cell(pal_t, 'Gross Profit', 1)
            gross_profit_y2 = self._cell(pal_t, 'Gross Profit', 2)
            gross_profit_y3 = self._cell(pal_t, 'Gross Profit', 3)
            sga_margin_y0 = round(strict_divide(sga_y0, gross_profit_y0) * 100, 2)
            sga_margin_y1 = round(strict_divide(sga_y1, gross_profit_y1) * 100, 2)
            sga_margin_y2 = round(strict_divide(sga_y2, gross_profit_y2) * 100, 2)
            sga_margin_y3 = round(strict_divide(sga_y3, gross_profit_y3) * 100, 2)
            if gross_profit_y0 <= 0 or gross_profit_y1 <= 0 or gross_profit_y2 <= 0 or (gross_profit_y3 <= 0):
                self.fundamentals['sellingGeneralAdministrativeMarginHistory'] = ([], [])
                w.append(Score.w_SGA)
                p.append(Score.w_SGA * Score.pf_mod)
                return Markup("⛔ SGA Margin (SGA/GP): Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ SGA Margin not calculated.")
            else:
                self.fundamentals['sellingGeneralAdministrativeMarginHistory'] = ([self.y3, self.y2, self.y1, self.y0], [sga_margin_y3, sga_margin_y2, sga_margin_y1, sga_margin_y0])
                if (sga_margin_y0 >= 30 or sga_margin_y1 >= 30 or sga_margin_y2 >= 30 or (sga_margin_y3 >= 30)) and (sga_margin_y0 < sga_margin_y1 and sga_margin_y1 < sga_margin_y2 and (sga_margin_y2 < sga_margin_y3)):
                    w.append(Score.w_SGA)
                    p.append(Score.w_SGA * Score.pf_mod)
                    w.append(Score.w_SGA_decreasing)
                    p.append(Score.w_SGA_decreasing * Score.pf_pos)
                    return Markup("⛔ SGA Margin (SGA/GP) ≥ 30%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(sga_margin_y3) + '%, ' + str(sga_margin_y2) + '%, ' + str(sga_margin_y1) + '%, ' + str(sga_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: SGA Margin consistently decreasing")
                elif (sga_margin_y0 >= 30 or sga_margin_y1 >= 30 or sga_margin_y2 >= 30 or (sga_margin_y3 >= 30)) and sga_margin_y0 < 30:
                    w.append(Score.w_SGA)
                    p.append(Score.w_SGA * Score.pf_mod)
                    return Markup("⛔ SGA Margin (SGA/GP) ≥ 30%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(sga_margin_y3) + '%, ' + str(sga_margin_y2) + '%, ' + str(sga_margin_y1) + '%, ' + str(sga_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: SGA Margin " + str(self.y0) + ' < 30% (' + str(sga_margin_y0) + '%)')
                elif sga_margin_y0 >= 30 or sga_margin_y1 >= 30 or sga_margin_y2 >= 30 or (sga_margin_y3 >= 30):
                    w.append(Score.w_SGA)
                    p.append(Score.w_SGA * Score.pf_neg)
                    return Markup("⛔ SGA Margin (SGA/GP) ≥ 30%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(sga_margin_y3) + '%, ' + str(sga_margin_y2) + '%, ' + str(sga_margin_y1) + '%, ' + str(sga_margin_y0) + '%')
                elif (sga_margin_y0 < 30 and sga_margin_y1 < 30 and (sga_margin_y2 < 30) and (sga_margin_y3 < 30)) and (sga_margin_y0 > sga_margin_y1 and sga_margin_y1 > sga_margin_y2 and (sga_margin_y2 > sga_margin_y3)):
                    w.append(Score.w_SGA)
                    p.append(Score.w_SGA * Score.pf_pos)
                    w.append(Score.w_SGA_increasing)
                    p.append(Score.w_SGA_increasing * Score.pf_neg)
                    return Markup("✅ SGA Margin (SGA/GP) < 30%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(sga_margin_y3) + '%, ' + str(sga_margin_y2) + '%, ' + str(sga_margin_y1) + '%, ' + str(sga_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: SGA Margin consistently increasing")
                elif sga_margin_y0 < 30 and sga_margin_y1 < 30 and (sga_margin_y2 < 30) and (sga_margin_y3 < 30):
                    w.append(Score.w_SGA)
                    p.append(Score.w_SGA * Score.pf_pos)
                    return Markup("✅ SGA Margin (SGA/GP) < 30%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(sga_margin_y3) + '%, ' + str(sga_margin_y2) + '%, ' + str(sga_margin_y1) + '%, ' + str(sga_margin_y0) + '%')
        except:
            w.append(Score.w_SGA)
            p.append(Score.w_SGA * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about SGA Margin!")

    def researchAndDevelopmentHistory(self):
        """ R&D = 0 or minimal (NB: for growth stock: R&D is important!!): R&D/gross profit < 30% (?) """
        pal_t = self.pal_t
        w = self.weights_list
        p = self.points_list
        try:
            rad_y0 = self._cell(pal_t, 'Research Development', 0)
            rad_y1 = self._cell(pal_t, 'Research Development', 1)
            rad_y2 = self._cell(pal_t, 'Research Development', 2)
            rad_y3 = self._cell(pal_t, 'Research Development', 3)
            gross_profit_y0 = self._cell(pal_t, 'Gross Profit', 0)
            gross_profit_y1 = self._cell(pal_t, 'Gross Profit', 1)
            gross_profit_y2 = self._cell(pal_t, 'Gross Profit', 2)
            gross_profit_y3 = self._cell(pal_t, 'Gross Profit', 3)
            rad_margin_y0 = round(strict_divide(rad_y0, gross_profit_y0) * 100, 2)
            rad_margin_y1 = round(strict_divide(rad_y1, gross_profit_y1) * 100, 2)
            rad_margin_y2 = round(strict_divide(rad_y2, gross_profit_y2) * 100, 2)
            rad_margin_y3 = round(strict_divide(rad_y3, gross_profit_y3) * 100, 2)
            if gross_profit_y0 <= 0 or gross_profit_y1 <= 0 or gross_profit_y2 <= 0 or (gross_profit_y3 <= 0):
                self.fundamentals['researchAndDevelopmentHistory'] = ([], [])
                w.append(Score.w_RaD)
                p.append(Score.w_RaD * Score.pf_mod)
                return Markup("⛔ R&D Margin (R&D/GP): Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ R&D Margin not calculated.")
            else:
                self.fundamentals['researchAndDevelopmentHistory'] = ([self.y3, self.y2, self.y1, self.y0], [rad_margin_y3, rad_margin_y2, rad_margin_y1, rad_margin_y0])
                if (rad_margin_y0 >= 30 or rad_margin_y1 >= 30 or rad_margin_y2 >= 30 or (rad_margin_y3 >= 30)) and (rad_margin_y0 < rad_margin_y1 and rad_margin_y1 < rad_margin_y2 and (rad_margin_y2 < rad_margin_y3)):
                    w.append(Score.w_RaD)
                    p.append(Score.w_RaD * Score.pf_mod)
                    w.append(Score.w_RaD_decreasing)
                    p.append(Score.w_RaD_decreasing * Score.pf_pos)
                    return Markup("⛔ R&D Margin (R&D/GP) ≥ 30%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(rad_margin_y3) + '%, ' + str(rad_margin_y2) + '%, ' + str(rad_margin_y1) + '%, ' + str(rad_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: R&D Margin consistently decreasing")
                elif (rad_margin_y0 >= 30 or rad_margin_y1 >= 30 or rad_margin_y2 >= 30 or (rad_margin_y3 >= 30)) and rad_margin_y0 < 30:
                    w.append(Score.w_RaD)
                    p.append(Score.w_RaD * Score.pf_mod)
                    return Markup("⛔ R&D Margin (R&D/GP) ≥ 30%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(rad_margin_y3) + '%, ' + str(rad_margin_y2) + '%, ' + str(rad_margin_y1) + '%, ' + str(rad_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: R&D Margin " + str(self.y0) + ' < 30% (' + str(rad_margin_y0) + '%)')
                elif rad_margin_y0 >= 30 or rad_margin_y1 >= 30 or rad_margin_y2 >= 30 or (rad_margin_y3 >= 30):
                    w.append(Score.w_RaD)
                    p.append(Score.w_RaD * Score.pf_neg)
                    return Markup("⛔ R&D Margin (R&D/GP) ≥ 30%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(rad_margin_y3) + '%, ' + str(rad_margin_y2) + '%, ' + str(rad_margin_y1) + '%, ' + str(rad_margin_y0) + '%')
                elif (rad_margin_y0 < 30 and rad_margin_y1 < 30 and (rad_margin_y2 < 30) and (rad_margin_y3 < 30)) and (rad_margin_y0 > rad_margin_y1 and rad_margin_y1 > rad_margin_y2 and (rad_margin_y2 > rad_margin_y3)):
                    w.append(Score.w_RaD)
                    p.append(Score.w_RaD * Score.pf_pos)
                    w.append(Score.w_RaD_increasing)
                    p.append(Score.w_RaD_increasing * Score.pf_neg)
                    return Markup("✅ R&D Margin (R&D/GP) < 30%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(rad_margin_y3) + '%, ' + str(rad_margin_y2) + '%, ' + str(rad_margin_y1) + '%, ' + str(rad_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: R&D Margin consistently increasing")
                elif rad_margin_y0 < 30 and rad_margin_y1 < 30 and (rad_margin_y2 < 30) and (rad_margin_y3 < 30):
                    w.append(Score.w_RaD)
                    p.append(Score.w_RaD * Score.pf_pos)
                    return Markup("✅ R&D Margin (R&D/GP) < 30%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(rad_margin_y3) + '%, ' + str(rad_margin_y2) + '%, ' + str(rad_margin_y1) + '%, ' + str(rad_margin_y0) + '%')
        except:
            w.append(Score.w_RaD)
            p.append(Score.w_RaD * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about R&D Margin!")

    def capexToEarningsHistory(self):
        """ Capex/Net earnings < 50% (preferably < 25%) >10y """
        pal_t = self.pal_t
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            capex_y0 = -self._cell(cfs_t, 'Capital Expenditures', 0)
            capex_y1 = -self._cell(cfs_t, 'Capital Expenditures', 1)
            capex_y2 = -self._cell(cfs_t, 'Capital Expenditures', 2)
            capex_y3 = -self._cell(cfs_t, 'Capital Expenditures', 3)
            net_income_y0 = self._cell(pal_t, 'Net Income', 0)
            net_income_y1 = self._cell(pal_t, 'Net Income', 1)
            net_income_y2 = self._cell(pal_t, 'Net Income', 2)
            net_income_y3 = self._cell(pal_t, 'Net Income', 3)
            capex_to_earnings_y0 = round(strict_divide(capex_y0, net_income_y0) * 100, 2)
            capex_to_earnings_y1 = round(strict_divide(capex_y1, net_income_y1) * 100, 2)
            capex_to_earnings_y2 = round(strict_divide(capex_y2, net_income_y2) * 100, 2)
            capex_to_earnings_y3 = round(strict_divide(capex_y3, net_income_y3) * 100, 2)
            if net_income_y0 <= 0 or net_income_y1 <= 0 or net_income_y2 <= 0 or (net_income_y3 <= 0):
                self.fundamentals['capexToEarningsHistory'] = ([], [])
                w.append(Score.w_CapexNI)
                p.append(Score.w_CapexNI * Score.pf_mod)
                return Markup("⛔ Capex Margin (Capex/NI): Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ Capex Margin not calculated.")
            else:
                self.fundamentals['capexToEarningsHistory'] = ([self.y3, self.y2, self.y1, self.y0], [capex_to_earnings_y3, capex_to_earnings_y2, capex_to_earnings_y1, capex_to_earnings_y0])
                if net_income_y0 > 0 and capex_to_earnings_y0 < 0:
                    w.append(Score.w_CapexNI_y0_negative)
                    p.append(Score.w_CapexNI_y0_negative * Score.pf_neg)
                    return Markup(' Capex/NI ' + str(self.y0) + " is NEGATIVE => net capital spending is negative!<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: It may indicate property depreciation > spending on new equipment, which is a loss that can affect the company's overall health!")
                elif ((net_income_y0 > 0 and net_income_y1 > 0 and (net_income_y2 > 0) and (net_income_y3 > 0)) and (capex_to_earnings_y0 >= 50 or capex_to_earnings_y1 >= 50 or capex_to_earnings_y2 >= 50 or (capex_to_earnings_y3 >= 50))) and (capex_to_earnings_y0 < capex_to_earnings_y1 and capex_to_earnings_y1 < capex_to_earnings_y2 and (capex_to_earnings_y2 < capex_to_earnings_y3)):
                    w.append(Score.w_CapexNI)
                    p.append(Score.w_CapexNI * Score.pf_mod)
                    w.append(Score.w_CapexNI_decreasing)
                    p.append(Score.w_CapexNI_decreasing * Score.pf_pos)
                    return Markup("⛔ Capex Margin (Capex/NI) ≥ 50%<br>\t\t\t\t\t\t<span class='text-danger'>↳ Capex Margin (Capex/NI): " + str(self.y3) + '-' + str(self.y0) + ': ' + str(capex_to_earnings_y3) + '%, ' + str(capex_to_earnings_y2) + '%, ' + str(capex_to_earnings_y1) + '%, ' + str(capex_to_earnings_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Capex Margin consistently decreasing")
                elif ((net_income_y0 > 0 and net_income_y1 > 0 and (net_income_y2 > 0) and (net_income_y3 > 0)) and (capex_to_earnings_y0 >= 50 or capex_to_earnings_y1 >= 50 or capex_to_earnings_y2 >= 50 or (capex_to_earnings_y3 >= 50))) and capex_to_earnings_y0 < 50:
                    w.append(Score.w_CapexNI)
                    p.append(Score.w_CapexNI * Score.pf_mod)
                    return Markup("⛔ Capex Margin (Capex/NI) ≥ 50%<br>\t\t\t\t\t\t<span class='text-danger'>↳ Capex Margin (Capex/NI): " + str(self.y3) + '-' + str(self.y0) + ': ' + str(capex_to_earnings_y3) + '%, ' + str(capex_to_earnings_y2) + '%, ' + str(capex_to_earnings_y1) + '%, ' + str(capex_to_earnings_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Capex Margin " + str(self.y0) + ' < 50% (' + str(capex_to_earnings_y0) + '%)')
                elif (net_income_y0 > 0 and net_income_y1 > 0 and (net_income_y2 > 0) and (net_income_y3 > 0)) and (capex_to_earnings_y0 >= 50 or capex_to_earnings_y1 >= 50 or capex_to_earnings_y2 >= 50 or (capex_to_earnings_y3 >= 50)):
                    w.append(Score.w_CapexNI)
                    p.append(Score.w_CapexNI * Score.pf_neg)
                    return Markup("⛔ Capex Margin (Capex/NI) ≥ 50%<br>\t\t\t\t\t\t<span class='text-danger'>↳ Capex Margin (Capex/NI): " + str(self.y3) + '-' + str(self.y0) + ': ' + str(capex_to_earnings_y3) + '%, ' + str(capex_to_earnings_y2) + '%, ' + str(capex_to_earnings_y1) + '%, ' + str(capex_to_earnings_y0) + '%')
                elif ((net_income_y0 > 0 and net_income_y1 > 0 and (net_income_y2 > 0) and (net_income_y3 > 0)) and (capex_to_earnings_y0 < 50 and capex_to_earnings_y1 < 50 and (capex_to_earnings_y2 < 50) and (capex_to_earnings_y3 < 50))) and (capex_to_earnings_y0 > capex_to_earnings_y1 and capex_to_earnings_y1 > capex_to_earnings_y2 and (capex_to_earnings_y2 > capex_to_earnings_y3)):
                    p.append(Score.w_CapexNI * Score.pf_pos)
                    w.append(Score.w_CapexNI)
                    w.append(Score.w_CapexNI_increasing)
                    p.append(Score.w_CapexNI_increasing * Score.pf_neg)
                    return Markup("✅ Capex Margin (Capex/NI) < 50%<br>\t\t\t\t\t\t<span class='text-success'>↳ Capex Margin (Capex/NI): " + str(self.y3) + '-' + str(self.y0) + ': ' + str(capex_to_earnings_y3) + '%, ' + str(capex_to_earnings_y2) + '%, ' + str(capex_to_earnings_y1) + '%, ' + str(capex_to_earnings_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: Capex Margin consistently increasing")
                elif (net_income_y0 > 0 and net_income_y1 > 0 and (net_income_y2 > 0) and (net_income_y3 > 0)) and (capex_to_earnings_y0 < 50 and capex_to_earnings_y1 < 50 and (capex_to_earnings_y2 < 50) and (capex_to_earnings_y3 < 50)):
                    w.append(Score.w_CapexNI)
                    p.append(Score.w_CapexNI * Score.pf_pos)
                    return Markup("✅ Capex Margin (Capex/NI) < 50%<br>\t\t\t\t\t\t<span class='text-success'>↳ Capex Margin (Capex/NI): " + str(self.y3) + '-' + str(self.y0) + ': ' + str(capex_to_earnings_y3) + '%, ' + str(capex_to_earnings_y2) + '%, ' + str(capex_to_earnings_y1) + '%, ' + str(capex_to_earnings_y0) + '%')
                elif net_income_y0 < 0 or net_income_y1 < 0 or net_income_y2 < 0 or (net_income_y3 < 0):
                    self.fundamentals['capexToEarningsHistory'] = []
                    return Markup("❓ <span class='text-info'>Capex Margin (Capex/NI) NOT calculated (Net Income NEGATIVE)!")
        except:
            w.append(Score.w_CapexNI)
            p.append(Score.w_CapexNI * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Capex to Net Earnings!")

    def depreciationMarginHistory(self):
        """ Depreciation/gross profit < 10% """
        pal_t = self.pal_t
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            depreciation_y0 = self._cell(cfs_t, 'Depreciation', 0)
            depreciation_y1 = self._cell(cfs_t, 'Depreciation', 0)
            depreciation_y2 = self._cell(cfs_t, 'Depreciation', 0)
            depreciation_y3 = self._cell(cfs_t, 'Depreciation', 0)
            gross_profit_y0 = self._cell(pal_t, 'Gross Profit', 0)
            gross_profit_y1 = self._cell(pal_t, 'Gross Profit', 1)
            gross_profit_y2 = self._cell(pal_t, 'Gross Profit', 2)
            gross_profit_y3 = self._cell(pal_t, 'Gross Profit', 3)
            depreciation_margin_y0 = round(strict_divide(depreciation_y0, gross_profit_y0) * 100, 2)
            depreciation_margin_y1 = round(strict_divide(depreciation_y1, gross_profit_y1) * 100, 2)
            depreciation_margin_y2 = round(strict_divide(depreciation_y2, gross_profit_y2) * 100, 2)
            depreciation_margin_y3 = round(strict_divide(depreciation_y3, gross_profit_y3) * 100, 2)
            if gross_profit_y0 <= 0 or gross_profit_y1 <= 0 or gross_profit_y2 <= 0 or (gross_profit_y3 <= 0):
                self.fundamentals['depreciationMarginHistory'] = ([], [])
                w.append(Score.w_DepGP)
                p.append(Score.w_DepGP * Score.pf_mod)
                return Markup("⛔ Depreciation Margin (Dep./GP): Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ Depreciation Margin not calculated.")
            else:
                self.fundamentals['depreciationMarginHistory'] = ([self.y3, self.y2, self.y1, self.y0], [depreciation_margin_y3, depreciation_margin_y2, depreciation_margin_y1, depreciation_margin_y0])
                if (depreciation_margin_y0 >= 10 or depreciation_margin_y1 >= 10 or depreciation_margin_y2 >= 10 or (depreciation_margin_y3 >= 10)) and (depreciation_margin_y0 < depreciation_margin_y1 and depreciation_margin_y1 < depreciation_margin_y2 and (depreciation_margin_y2 < depreciation_margin_y3)):
                    w.append(Score.w_DepGP)
                    p.append(Score.w_DepGP * Score.pf_mod)
                    w.append(Score.w_DepGP_decreasing)
                    p.append(Score.w_DepGP_decreasing * Score.pf_pos)
                    return Markup("⛔ Depreciation Margin (Dep./GP) ≥ 10%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(depreciation_margin_y3) + '%, ' + str(depreciation_margin_y2) + '%, ' + str(depreciation_margin_y1) + '%, ' + str(depreciation_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Depreciation Margin consistently decreasing")
                elif (depreciation_margin_y0 >= 10 or depreciation_margin_y1 >= 10 or depreciation_margin_y2 >= 10 or (depreciation_margin_y3 >= 10)) and depreciation_margin_y0 < 10:
                    w.append(Score.w_DepGP)
                    p.append(Score.w_DepGP * Score.pf_mod)
                    return Markup("⛔ Depreciation Margin (Dep./GP) ≥ 10%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(depreciation_margin_y3) + '%, ' + str(depreciation_margin_y2) + '%, ' + str(depreciation_margin_y1) + '%, ' + str(depreciation_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Depreciation Margin " + str(self.y0) + ' < 10% (' + str(depreciation_margin_y0) + '%)')
                elif depreciation_margin_y0 >= 10 or depreciation_margin_y1 >= 10 or depreciation_margin_y2 >= 10 or (depreciation_margin_y3 >= 10):
                    w.append(Score.w_DepGP)
                    p.append(Score.w_DepGP * Score.pf_neg)
                    return Markup("⛔ Depreciation Margin (Dep./GP) ≥ 10%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(depreciation_margin_y3) + '%, ' + str(depreciation_margin_y2) + '%, ' + str(depreciation_margin_y1) + '%, ' + str(depreciation_margin_y0) + '%')
                elif (depreciation_margin_y0 < 10 and depreciation_margin_y1 < 10 and (depreciation_margin_y2 < 10) and (depreciation_margin_y3 < 10)) and (depreciation_margin_y0 > depreciation_margin_y1 and depreciation_margin_y1 > depreciation_margin_y2 and (depreciation_margin_y2 > depreciation_margin_y3)):
                    w.append(Score.w_DepGP)
                    p.append(Score.w_DepGP * Score.pf_pos)
                    w.append(Score.w_DepGP_increasing)
                    p.append(Score.w_DepGP_increasing * Score.pf_neg)
                    return Markup("✅ Depreciation Margin (Dep./GP) < 10%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(depreciation_margin_y3) + '%, ' + str(depreciation_margin_y2) + '%, ' + str(depreciation_margin_y1) + '%, ' + str(depreciation_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: Depreciation Margin consistently increasing")
                elif depreciation_margin_y0 < 10 and depreciation_margin_y1 < 10 and (depreciation_margin_y2 < 10) and (depreciation_margin_y3 < 10):
                    w.append(Score.w_DepGP)
                    p.append(Score.w_DepGP * Score.pf_pos)
                    return Markup("✅ Depreciation Margin (Dep./GP) < 10%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(depreciation_margin_y3) + '%, ' + str(depreciation_margin_y2) + '%, ' + str(depreciation_margin_y1) + '%, ' + str(depreciation_margin_y0) + '%')
        except:
            w.append(Score.w_DepGP)
            p.append(Score.w_DepGP * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Depreciation Margin!")

    def interestExpenseMarginHistory(self):
        """ Interest Expense/operating profit <10% (<30% : depends of sector (compare sector mean)) """
        pal_t = self.pal_t
        w = self.weights_list
        p = self.points_list
        try:
            interest_expense_y0 = -self._cell(pal_t, 'Interest Expense', 0)
            interest_expense_y1 = -self._cell(pal_t, 'Interest Expense', 1)
            interest_expense_y2 = -self._cell(pal_t, 'Interest Expense', 2)
            interest_expense_y3 = -self._cell(pal_t, 'Interest Expense', 3)
            operating_profit_y0 = self._cell(pal_t, 'Operating Income', 0)
            operating_profit_y1 = self._cell(pal_t, 'Operating Income', 1)
            operating_profit_y2 = self._cell(pal_t, 'Operating Income', 2)
            operating_profit_y3 = self._cell(pal_t, 'Operating Income', 3)
            interest_expense_margin_y0 = round(strict_divide(interest_expense_y0, operating_profit_y0) * 100, 2)
            interest_expense_margin_y1 = round(strict_divide(interest_expense_y1, operating_profit_y1) * 100, 2)
            interest_expense_margin_y2 = round(strict_divide(interest_expense_y2, operating_profit_y2) * 100, 2)
            interest_expense_margin_y3 = round(strict_divide(interest_expense_y3, operating_profit_y3) * 100, 2)
            if operating_profit_y0 <= 0 or operating_profit_y1 <= 0 or operating_profit_y2 <= 0 or (operating_profit_y3 <= 0):
                self.fundamentals['interestExpenseMarginHistory'] = ([], [])
                w.append(Score.w_IEOP)
                p.append(Score.w_IEOP * Score.pf_mod)
                return Markup("⛔ Interest Expense Margin (IE/OP): Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ Interest Expense Margin not calculated.")
            else:
                self.fundamentals['interestExpenseMarginHistory'] = ([self.y3, self.y2, self.y1, self.y0], [interest_expense_margin_y3, interest_expense_margin_y2, interest_expense_margin_y1, interest_expense_margin_y0])
                if (interest_expense_margin_y0 >= 10 or interest_expense_margin_y1 >= 10 or interest_expense_margin_y2 >= 10 or (interest_expense_margin_y3 >= 10)) and (interest_expense_margin_y0 < interest_expense_margin_y1 and interest_expense_margin_y1 < interest_expense_margin_y2 and (interest_expense_margin_y2 < interest_expense_margin_y3)):
                    w.append(Score.w_IEOP)
                    p.append(Score.w_IEOP * Score.pf_mod)
                    w.append(Score.w_IEOP_decreasing)
                    p.append(Score.w_IEOP_decreasing * Score.pf_pos)
                    return Markup("⛔ Interest Expense Margin (IE/OP) ≥ 10% (depends on sector!)<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(interest_expense_margin_y3) + '%, ' + str(interest_expense_margin_y2) + '%, ' + str(interest_expense_margin_y1) + '%, ' + str(interest_expense_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Interest Expense Margin consistently decreasing")
                elif (interest_expense_margin_y0 >= 10 or interest_expense_margin_y1 >= 10 or interest_expense_margin_y2 >= 10 or (interest_expense_margin_y3 >= 10)) and interest_expense_margin_y0 < 10:
                    w.append(Score.w_IEOP)
                    p.append(Score.w_IEOP * Score.pf_mod)
                    return Markup("⛔ Interest Expense Margin (IE/OP) ≥ 10% (depends on sector!)<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(interest_expense_margin_y3) + '%, ' + str(interest_expense_margin_y2) + '%, ' + str(interest_expense_margin_y1) + '%, ' + str(interest_expense_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Interest Expense Margin " + str(self.y0) + ' < 10% (' + str(interest_expense_margin_y0) + '%)')
                elif interest_expense_margin_y0 >= 10 or interest_expense_margin_y1 >= 10 or interest_expense_margin_y2 >= 10 or (interest_expense_margin_y3 >= 10):
                    w.append(Score.w_IEOP)
                    p.append(Score.w_IEOP * Score.pf_neg)
                    return Markup("⛔ Interest Expense Margin (IE/OP) ≥ 10% (depends on sector!)<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(interest_expense_margin_y3) + '%, ' + str(interest_expense_margin_y2) + '%, ' + str(interest_expense_margin_y1) + '%, ' + str(interest_expense_margin_y0) + '%')
                elif (interest_expense_margin_y0 < 10 and interest_expense_margin_y1 < 10 and (interest_expense_margin_y2 < 10) and (interest_expense_margin_y3 < 10)) and (interest_expense_margin_y0 > interest_expense_margin_y1 and interest_expense_margin_y1 > interest_expense_margin_y2 and (interest_expense_margin_y2 > interest_expense_margin_y3)):
                    w.append(Score.w_IEOP)
                    p.append(Score.w_IEOP * Score.pf_pos)
                    w.append(Score.w_IEOP_increasing)
                    p.append(Score.w_IEOP_increasing * Score.pf_neg)
                    return Markup("✅ Interest Expense Margin (IE/OP) < 10%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(interest_expense_margin_y3) + '%, ' + str(interest_expense_margin_y2) + '%, ' + str(interest_expense_margin_y1) + '%, ' + str(interest_expense_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: Interest Expense Margin consistently increasing")
                elif interest_expense_margin_y0 < 10 and interest_expense_margin_y1 < 10 and (interest_expense_margin_y2 < 10) and (interest_expense_margin_y3 < 10):
                    w.append(Score.w_IEOP)
                    p.append(Score.w_IEOP * Score.pf_pos)
                    return Markup("✅ Interest Expense Margin (IE/OP) < 10%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(interest_expense_margin_y3) + '%, ' + str(interest_expense_margin_y2) + '%, ' + str(interest_expense_margin_y1) + '%, ' + str(interest_expense_margin_y0) + '%')
        except:
            w.append(Score.w_IEOP)
            p.append(Score.w_IEOP * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Interest Expense Margin!")

    def netReceivablesMarginHistory(self):
        """ Net Receivables/Sales (<20%): Consistent (>7y) low (<20%) = fast collection of money
			NB: net receivables on B/S is snapshot and Sales on P&L is total/y: better to use average net receivables but not ready available! """
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            net_receivables_y0 = self._cell(bs_t, 'Net Receivables', 0)
            net_receivables_y1 = self._cell(bs_t, 'Net Receivables', 1)
            net_receivables_y2 = self._cell(bs_t, 'Net Receivables', 2)
            net_receivables_y3 = self._cell(bs_t, 'Net Receivables', 3)
            total_revenue_y0 = self._cell(pal_t, 'Total Revenue', 0)
            total_revenue_y1 = self._cell(pal_t, 'Total Revenue', 1)
            total_revenue_y2 = self._cell(pal_t, 'Total Revenue', 2)
            total_revenue_y3 = self._cell(pal_t, 'Total Revenue', 3)
            net_receivables_margin_y0 = round(strict_divide(net_receivables_y0, total_revenue_y0) * 100, 2)
            net_receivables_margin_y1 = round(strict_divide(net_receivables_y1, total_revenue_y1) * 100, 2)
            net_receivables_margin_y2 = round(strict_divide(net_receivables_y2, total_revenue_y2) * 100, 2)
            net_receivables_margin_y3 = round(strict_divide(net_receivables_y3, total_revenue_y3) * 100, 2)
            if total_revenue_y0 <= 0 or total_revenue_y1 <= 0 or total_revenue_y2 <= 0 or (total_revenue_y3 <= 0):
                self.fundamentals['netReceivablesMarginHistory'] = ([], [])
                w.append(Score.w_ARRev)
                p.append(Score.w_ARRev * Score.pf_mod)
                return Markup("⛔ Net Receivables Margin (Acc.Receiv./Sales): Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ Net Receivables Margin not calculated.")
            else:
                self.fundamentals['netReceivablesMarginHistory'] = ([self.y3, self.y2, self.y1, self.y0], [net_receivables_margin_y3, net_receivables_margin_y2, net_receivables_margin_y1, net_receivables_margin_y0])
                ' CAVE liberal accounting policies / accounting fraud! '
                nrm_list = [net_receivables_margin_y0, net_receivables_margin_y1, net_receivables_margin_y2, net_receivables_margin_y3]
                nrm_max = max(nrm_list)
                nrm_triggered_mean = strict_divide(sum(nrm_list) - nrm_max, len(nrm_list) - 1)
                nrm_cave = nrm_triggered_mean * (1 + 0.4)
                if (net_receivables_margin_y0 >= 20 or net_receivables_margin_y1 >= 20 or net_receivables_margin_y2 >= 20 or (net_receivables_margin_y3 >= 20)) and (net_receivables_margin_y0 < net_receivables_margin_y1 and net_receivables_margin_y1 < net_receivables_margin_y2 and (net_receivables_margin_y2 < net_receivables_margin_y3)):
                    w.append(Score.w_ARRev)
                    p.append(Score.w_ARRev * Score.pf_mod)
                    w.append(Score.w_ARRev_decreasing)
                    p.append(Score.w_ARRev_decreasing * Score.pf_pos)
                    return Markup("⛔ Net Receivables Margin (Acc.Receiv./Sales) ≥ 20%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(net_receivables_margin_y3) + '%, ' + str(net_receivables_margin_y2) + '%, ' + str(net_receivables_margin_y1) + '%, ' + str(net_receivables_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Net Receivables Margin consistently decreasing")
                elif (net_receivables_margin_y0 >= 20 or net_receivables_margin_y1 >= 20 or net_receivables_margin_y2 >= 20 or (net_receivables_margin_y3 >= 20)) and net_receivables_margin_y0 < 20:
                    w.append(Score.w_ARRev)
                    p.append(Score.w_ARRev * Score.pf_mod)
                    return Markup("⛔ Net Receivables Margin (Acc.Receiv./Sales) ≥ 20%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(net_receivables_margin_y3) + '%, ' + str(net_receivables_margin_y2) + '%, ' + str(net_receivables_margin_y1) + '%, ' + str(net_receivables_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Net Receivables Margin < 20% " + str(self.y0) + ' (' + str(net_receivables_margin_y0) + '%)')
                elif (net_receivables_margin_y0 >= 20 or net_receivables_margin_y1 >= 20 or net_receivables_margin_y2 >= 20 or (net_receivables_margin_y3 >= 20)) and (net_receivables_margin_y0 > nrm_cave or net_receivables_margin_y1 > nrm_cave or net_receivables_margin_y2 > nrm_cave or (net_receivables_margin_y3 > nrm_cave)):
                    w.append(Score.w_ARRev)
                    p.append(Score.w_ARRev * Score.pf_neg)
                    return Markup("⛔ Net Receivables Margin (Acc.Receiv./Sales) ≥ 20%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(net_receivables_margin_y3) + '%, ' + str(net_receivables_margin_y2) + '%, ' + str(net_receivables_margin_y1) + '%, ' + str(net_receivables_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: Aberrant NRM value => liberal accounting policies/accounting fraud?")
                elif net_receivables_margin_y0 >= 20 or net_receivables_margin_y1 >= 20 or net_receivables_margin_y2 >= 20 or (net_receivables_margin_y3 >= 20):
                    w.append(Score.w_ARRev)
                    p.append(Score.w_ARRev * Score.pf_neg)
                    return Markup("⛔ Net Receivables Margin (Acc.Receiv./Sales) ≥ 20%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(net_receivables_margin_y3) + '%, ' + str(net_receivables_margin_y2) + '%, ' + str(net_receivables_margin_y1) + '%, ' + str(net_receivables_margin_y0) + '%')
                elif (net_receivables_margin_y0 < 20 and net_receivables_margin_y1 < 20 and (net_receivables_margin_y2 < 20) and (net_receivables_margin_y3 < 20)) and (net_receivables_margin_y0 > net_receivables_margin_y1 and net_receivables_margin_y1 > net_receivables_margin_y2 and (net_receivables_margin_y2 > net_receivables_margin_y3)):
                    w.append(Score.w_ARRev)
                    p.append(Score.w_ARRev * Score.pf_pos)
                    w.append(Score.w_ARRev_increasing)
                    p.append(Score.w_ARRev_increasing * Score.pf_neg)
                    return Markup("✅ Net Receivables Margin (Acc.Receiv./Sales) < 20%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(net_receivables_margin_y3) + '%, ' + str(net_receivables_margin_y2) + '%, ' + str(net_receivables_margin_y1) + '%, ' + str(net_receivables_margin_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: Net Receivables Margin consistently increasing")
                elif net_receivables_margin_y0 < 20 and net_receivables_margin_y1 < 20 and (net_receivables_margin_y2 < 20) and (net_receivables_margin_y3 < 20):
                    w.append(Score.w_ARRev)
                    p.append(Score.w_ARRev * Score.pf_pos)
                    return Markup("✅ Net Receivables Margin (Acc.Receiv./Sales) < 20%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(net_receivables_margin_y3) + '%, ' + str(net_receivables_margin_y2) + '%, ' + str(net_receivables_margin_y1) + '%, ' + str(net_receivables_margin_y0) + '%')
        except:
            w.append(Score.w_ARRev)
            p.append(Score.w_ARRev * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Net Receivables Margin!")

    def currentRatioHistory(self):
        """ Current ratio (CR): CA/CL ≥ 1 (except cash machines) """
        data = self.data
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            total_current_assets_y0 = self._cell(bs_t, 'Total Current Assets', 0)
            total_current_assets_y1 = self._cell(bs_t, 'Total Current Assets', 1)
            total_current_assets_y2 = self._cell(bs_t, 'Total Current Assets', 2)
            total_current_assets_y3 = self._cell(bs_t, 'Total Current Assets', 3)
            total_current_liabilities_y0 = self._cell(bs_t, 'Total Current Liabilities', 0)
            total_current_liabilities_y1 = self._cell(bs_t, 'Total Current Liabilities', 1)
            total_current_liabilities_y2 = self._cell(bs_t, 'Total Current Liabilities', 2)
            total_current_liabilities_y3 = self._cell(bs_t, 'Total Current Liabilities', 3)
            cr_y0 = round(strict_divide(total_current_assets_y0, total_current_liabilities_y0), 2)
            cr_y1 = round(strict_divide(total_current_assets_y1, total_current_liabilities_y1), 2)
            cr_y2 = round(strict_divide(total_current_assets_y2, total_current_liabilities_y2), 2)
            cr_y3 = round(strict_divide(total_current_assets_y3, total_current_liabilities_y3), 2)
            if total_current_liabilities_y0 <= 0 or total_current_liabilities_y1 <= 0 or total_current_liabilities_y2 <= 0 or (total_current_liabilities_y3 <= 0):
                self.fundamentals['currentRatioHistory'] = ([], [])
                w.append(Score.w_CR)
                p.append(Score.w_CR * Score.pf_mod)
                return Markup("⛔ Current Ratio (CA/CL): Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ Current Ratio not calculated.")
            else:
                self.fundamentals['currentRatioHistory'] = ([self.y3, self.y2, self.y1, self.y0], [cr_y3, cr_y2, cr_y1, cr_y0])
                if (cr_y0 < 1 or cr_y1 < 1 or cr_y2 < 1 or (cr_y3 < 1)) and (cr_y0 > cr_y1 and cr_y1 > cr_y2 and (cr_y2 > cr_y3)):
                    w.append(Score.w_CR)
                    p.append(Score.w_CR * Score.pf_mod)
                    w.append(Score.w_CR_increasing)
                    p.append(Score.w_CR_increasing * Score.pf_pos)
                    return Markup("⛔ Current Ratio (CA/CL) < 1<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cr_y3) + ', ' + str(cr_y2) + ', ' + str(cr_y1) + ', ' + str(cr_y0) + "<br>\t\t\t\t\t\t<span class='text-success'>↳ although: CR consistently increasing")
                elif (cr_y0 < 1 or cr_y1 < 1 or cr_y2 < 1 or (cr_y3 < 1)) and cr_y0 >= 1:
                    w.append(Score.w_CR)
                    p.append(Score.w_CR * Score.pf_mod)
                    return Markup("⛔ Current Ratio (CA/CL) < 1<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cr_y3) + ', ' + str(cr_y2) + ', ' + str(cr_y1) + ', ' + str(cr_y0) + "<br>\t\t\t\t\t\t<span class='text-success'>↳ although: CR " + str(self.y0) + ' ≥ 1 (' + str(cr_y0) + ')')
                elif cr_y0 < 1 or cr_y1 < 1 or cr_y2 < 1 or (cr_y3 < 1):
                    w.append(Score.w_CR)
                    p.append(Score.w_CR * Score.pf_neg)
                    return Markup("⛔ Current Ratio (CA/CL) < 1<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cr_y3) + ', ' + str(cr_y2) + ', ' + str(cr_y1) + ', ' + str(cr_y0))
                elif (cr_y0 >= 1 and cr_y1 >= 1 and (cr_y2 >= 1) and (cr_y3 >= 1)) and (cr_y0 < cr_y1 and cr_y1 < cr_y2 and (cr_y2 < cr_y3)):
                    w.append(Score.w_CR)
                    p.append(Score.w_CR * Score.pf_pos)
                    w.append(Score.w_CR_decreasing)
                    p.append(Score.w_CR_decreasing * Score.pf_neg)
                    return Markup("✅ Current Ratio (CA/CL) ≥ 1<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cr_y3) + ', ' + str(cr_y2) + ', ' + str(cr_y1) + ', ' + str(cr_y0) + "<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: CR consistently decreasing")
                elif cr_y0 >= 1 and cr_y1 >= 1 and (cr_y2 >= 1) and (cr_y3 >= 1):
                    w.append(Score.w_CR)
                    p.append(Score.w_CR * Score.pf_pos)
                    return Markup("✅ Current Ratio (CA/CL) ≥ 1<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cr_y3) + ', ' + str(cr_y2) + ', ' + str(cr_y1) + ', ' + str(cr_y0))
        except:
            w.append(Score.w_CR)
            p.append(Score.w_CR * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about CR!")

    def quickRatioHistory(self):
        """ Quick Ratio (= Acid-Test Ratio) ≥ 0.8 (except cash machines)
		= (Total Current Assets - Inventory - Other Current Assets) / Total Current Liabilities
		= (Cash + Short Term Investments + Net Receivables) / Total Current Liabilities """
        data = self.data
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            cash_y0 = self._cell(bs_t, 'Cash', 0)
            cash_y1 = self._cell(bs_t, 'Cash', 1)
            cash_y2 = self._cell(bs_t, 'Cash', 2)
            cash_y3 = self._cell(bs_t, 'Cash', 3)
            short_term_investments_y0 = self._cell(bs_t, 'Short Term Investments', 0)
            short_term_investments_y1 = self._cell(bs_t, 'Short Term Investments', 1)
            short_term_investments_y2 = self._cell(bs_t, 'Short Term Investments', 2)
            short_term_investments_y3 = self._cell(bs_t, 'Short Term Investments', 3)
            net_receivables_y0 = self._cell(bs_t, 'Net Receivables', 0)
            net_receivables_y1 = self._cell(bs_t, 'Net Receivables', 1)
            net_receivables_y2 = self._cell(bs_t, 'Net Receivables', 2)
            net_receivables_y3 = self._cell(bs_t, 'Net Receivables', 3)
            total_current_liabilities_y0 = self._cell(bs_t, 'Total Current Liabilities', 0)
            total_current_liabilities_y1 = self._cell(bs_t, 'Total Current Liabilities', 1)
            total_current_liabilities_y2 = self._cell(bs_t, 'Total Current Liabilities', 2)
            total_current_liabilities_y3 = self._cell(bs_t, 'Total Current Liabilities', 3)
            qr_y0 = round(strict_divide(cash_y0 + short_term_investments_y0 + net_receivables_y0, total_current_liabilities_y0), 2)
            qr_y1 = round(strict_divide(cash_y1 + short_term_investments_y1 + net_receivables_y1, total_current_liabilities_y1), 2)
            qr_y2 = round(strict_divide(cash_y2 + short_term_investments_y2 + net_receivables_y2, total_current_liabilities_y2), 2)
            qr_y3 = round(strict_divide(cash_y3 + short_term_investments_y3 + net_receivables_y3, total_current_liabilities_y3), 2)
            if total_current_liabilities_y0 <= 0 or total_current_liabilities_y1 <= 0 or total_current_liabilities_y2 <= 0 or (total_current_liabilities_y3 <= 0):
                self.fundamentals['quickRatioHistory'] = ([], [])
                w.append(Score.w_QR)
                p.append(Score.w_QR * Score.pf_mod)
                return Markup("⛔ Quick Ratio: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ Quick Ratio not calculated.")
            else:
                self.fundamentals['quickRatioHistory'] = ([self.y3, self.y2, self.y1, self.y0], [qr_y3, qr_y2, qr_y1, qr_y0])
                if (qr_y0 < 0.8 or qr_y1 < 0.8 or qr_y2 < 0.8 or (qr_y3 < 0.8)) and (qr_y0 > qr_y1 and qr_y1 > qr_y2 and (qr_y2 > qr_y3)):
                    w.append(Score.w_QR)
                    p.append(Score.w_QR * Score.pf_mod)
                    w.append(Score.w_QR_increasing)
                    p.append(Score.w_QR_increasing * Score.pf_pos)
                    return Markup("⛔ Quick Ratio < 0.8<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(qr_y3) + ', ' + str(qr_y2) + ', ' + str(qr_y1) + ', ' + str(qr_y0) + "<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Quick Ratio consistently increasing")
                elif (qr_y0 < 0.8 or qr_y1 < 0.8 or qr_y2 < 0.8 or (qr_y3 < 0.8)) and qr_y0 >= 0.8:
                    w.append(Score.w_QR)
                    p.append(Score.w_QR * Score.pf_mod)
                    return Markup("⛔ Quick Ratio < 0.8<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(qr_y3) + ', ' + str(qr_y2) + ', ' + str(qr_y1) + ', ' + str(qr_y0) + "<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Quick Ratio " + str(self.y0) + ' ≥ 0.8 (' + str(qr_y0) + ')')
                elif qr_y0 < 0.8 or qr_y1 < 0.8 or qr_y2 < 0.8 or (qr_y3 < 0.8):
                    w.append(Score.w_QR)
                    p.append(Score.w_QR * Score.pf_neg)
                    return Markup("⛔ Quick Ratio < 0.8<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(qr_y3) + ', ' + str(qr_y2) + ', ' + str(qr_y1) + ', ' + str(qr_y0))
                elif (qr_y0 >= 0.8 and qr_y1 >= 0.8 and (qr_y2 >= 0.8) and (qr_y3 >= 0.8)) and (qr_y0 < qr_y1 and qr_y1 < qr_y2 and (qr_y2 < qr_y3)):
                    w.append(Score.w_QR)
                    p.append(Score.w_QR * Score.pf_pos)
                    w.append(Score.w_QR_decreasing)
                    p.append(Score.w_QR_decreasing * Score.pf_neg)
                    return Markup("✅ Quick Ratio ≥ 0.8<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(qr_y3) + ', ' + str(qr_y2) + ', ' + str(qr_y1) + ', ' + str(qr_y0) + "<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: Quick Ratio consistently decreasing")
                elif qr_y0 >= 0.8 and qr_y1 >= 0.8 and (qr_y2 >= 0.8) and (qr_y3 >= 0.8):
                    w.append(Score.w_QR)
                    p.append(Score.w_QR * Score.pf_pos)
                    return Markup("✅ Quick Ratio ≥ 0.8<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(qr_y3) + ', ' + str(qr_y2) + ', ' + str(qr_y1) + ', ' + str(qr_y0))
        except:
            w.append(Score.w_QR)
            p.append(Score.w_QR * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Quick Ratio!")

    def totalCashToMonthlyOperatingExpensesHistory(self):
        """ Cash: consistent safe amount on hand >7y
			NB: General rule of thumb: The business should have 3 to 6 months’ worth of operating expenses in cash at any given time. """
        data = self.data
        pal_t = self.pal_t
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            cash_y0 = self._cell(bs_t, 'Cash', 0)
            cash_y1 = self._cell(bs_t, 'Cash', 1)
            cash_y2 = self._cell(bs_t, 'Cash', 2)
            cash_y3 = self._cell(bs_t, 'Cash', 3)
            total_operating_expenses_y0 = self._cell(pal_t, 'Total Operating Expenses', 0)
            total_operating_expenses_y1 = self._cell(pal_t, 'Total Operating Expenses', 1)
            total_operating_expenses_y2 = self._cell(pal_t, 'Total Operating Expenses', 2)
            total_operating_expenses_y3 = self._cell(pal_t, 'Total Operating Expenses', 3)
            cash_on_hand_y0 = round(strict_divide(cash_y0, strict_divide(total_operating_expenses_y0, 12)), 2)
            cash_on_hand_y1 = round(strict_divide(cash_y1, strict_divide(total_operating_expenses_y1, 12)), 2)
            cash_on_hand_y2 = round(strict_divide(cash_y2, strict_divide(total_operating_expenses_y2, 12)), 2)
            cash_on_hand_y3 = round(strict_divide(cash_y3, strict_divide(total_operating_expenses_y3, 12)), 2)
            if total_operating_expenses_y0 <= 0 or total_operating_expenses_y1 <= 0 or total_operating_expenses_y2 <= 0 or (total_operating_expenses_y3 <= 0):
                self.fundamentals['totalCashToMonthlyOperatingExpensesHistory'] = ([], [])
                w.append(Score.w_Cash)
                p.append(Score.w_Cash * Score.pf_mod)
                return Markup("⛔ Cash/M.Op.Exp.: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ Cash/M.Op.Exp. not calculated.")
            else:
                self.fundamentals['totalCashToMonthlyOperatingExpensesHistory'] = ([self.y3, self.y2, self.y1, self.y0], [cash_on_hand_y3, cash_on_hand_y2, cash_on_hand_y1, cash_on_hand_y0])
                if (cash_on_hand_y0 < 3 or cash_on_hand_y1 < 3 or cash_on_hand_y2 < 3 or (cash_on_hand_y3 < 3)) and (cash_on_hand_y0 > cash_on_hand_y1 and cash_on_hand_y1 > cash_on_hand_y2 and (cash_on_hand_y2 > cash_on_hand_y3)):
                    w.append(Score.w_Cash)
                    p.append(Score.w_Cash * Score.pf_mod)
                    w.append(Score.w_Cash_increasing)
                    p.append(Score.w_Cash_increasing * Score.pf_pos)
                    return Markup("⛔ Cash/M.Op.Exp. < 3<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cash_on_hand_y3) + ', ' + str(cash_on_hand_y2) + ', ' + str(cash_on_hand_y1) + ', ' + str(cash_on_hand_y0) + "<br>\t\t\t\t\t\t<span class='text-danger'>↳ Insufficient cash on hand to cover 3 months of total operating expenses!<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Cash/M.Op.Exp. consistently increasing")
                elif (cash_on_hand_y0 < 3 or cash_on_hand_y1 < 3 or cash_on_hand_y2 < 3 or (cash_on_hand_y3 < 3)) and cash_on_hand_y0 >= 3:
                    w.append(Score.w_Cash)
                    p.append(Score.w_Cash * Score.pf_mod)
                    return Markup("⛔ Cash/M.Op.Exp. < 3<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cash_on_hand_y3) + ', ' + str(cash_on_hand_y2) + ', ' + str(cash_on_hand_y1) + ', ' + str(cash_on_hand_y0) + "<br>\t\t\t\t\t\t<span class='text-danger'>↳ Insufficient cash on hand to cover 3 months of total operating expenses!<br>\t\t\t\t\t\t<span class='text-success'>↳ although: Cash/M.Op.Exp. " + str(self.y0) + ' ≥ 3 (' + str(cash_on_hand_y0) + ")<br>\t\t\t\t\t\t<span class='text-success'>↳ Sufficient cash (ttm) on hand to cover 3 months of total operating expenses!")
                elif cash_on_hand_y0 < 3 or cash_on_hand_y1 < 3 or cash_on_hand_y2 < 3 or (cash_on_hand_y3 < 3):
                    w.append(Score.w_Cash)
                    p.append(Score.w_Cash * Score.pf_neg)
                    return Markup("⛔ Cash/M.Op.Exp. < 3<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cash_on_hand_y3) + ', ' + str(cash_on_hand_y2) + ', ' + str(cash_on_hand_y1) + ', ' + str(cash_on_hand_y0) + "<br>\t\t\t\t\t\t<span class='text-danger'>↳ Insufficient cash on hand to cover 3 months of total operating expenses!")
                elif (cash_on_hand_y0 >= 3 and cash_on_hand_y1 >= 3 and (cash_on_hand_y2 >= 3) and (cash_on_hand_y3 >= 3)) and (cash_on_hand_y0 < cash_on_hand_y1 and cash_on_hand_y1 < cash_on_hand_y2 and (cash_on_hand_y2 < cash_on_hand_y3)):
                    w.append(Score.w_Cash)
                    p.append(Score.w_Cash * Score.pf_pos)
                    w.append(Score.w_Cash_decreasing)
                    p.append(Score.w_Cash_decreasing * Score.pf_neg)
                    return Markup("✅ Cash/M.Op.Exp. ≥ 3<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cash_on_hand_y3) + ', ' + str(cash_on_hand_y2) + ', ' + str(cash_on_hand_y1) + ', ' + str(cash_on_hand_y0) + "<br>\t\t\t\t\t\t<span class='text-success'>↳ Sufficient cash on hand to cover 3 months of total operating expenses!<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: Cash/M.Op.Exp. consistently decreasing")
                elif cash_on_hand_y0 >= 3 and cash_on_hand_y1 >= 3 and (cash_on_hand_y2 >= 3) and (cash_on_hand_y3 >= 3):
                    w.append(Score.w_Cash)
                    p.append(Score.w_Cash * Score.pf_pos)
                    return Markup("✅ Cash/M.Op.Exp. ≥ 3<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(cash_on_hand_y3) + ', ' + str(cash_on_hand_y2) + ', ' + str(cash_on_hand_y1) + ', ' + str(cash_on_hand_y0) + "<br>\t\t\t\t\t\t<span class='text-success'>↳ Sufficient cash on hand to cover 3 months of total operating expenses!")
        except:
            w.append(Score.w_Cash)
            p.append(Score.w_Cash * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Cash/Monthly Total Operational Expenses!")

    def debtToEquityHistory(self):
        """ D/E ≤ 50% (?) """
        data = self.data
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            long_term_debt_y0 = self._cell(bs_t, 'Long Term Debt', 0)
            long_term_debt_y1 = self._cell(bs_t, 'Long Term Debt', 1)
            long_term_debt_y2 = self._cell(bs_t, 'Long Term Debt', 2)
            long_term_debt_y3 = self._cell(bs_t, 'Long Term Debt', 3)
            equity_y0 = self._cell(bs_t, 'Total Stockholder Equity', 0)
            equity_y1 = self._cell(bs_t, 'Total Stockholder Equity', 1)
            equity_y2 = self._cell(bs_t, 'Total Stockholder Equity', 2)
            equity_y3 = self._cell(bs_t, 'Total Stockholder Equity', 3)
            dte_ttm = data['debtToEquity']
            dte_y0 = round(strict_divide(long_term_debt_y0, equity_y0) * 100, 2)
            dte_y1 = round(strict_divide(long_term_debt_y1, equity_y1) * 100, 2)
            dte_y2 = round(strict_divide(long_term_debt_y2, equity_y2) * 100, 2)
            dte_y3 = round(strict_divide(long_term_debt_y3, equity_y3) * 100, 2)
            if equity_y0 <= 0 or equity_y1 <= 0 or equity_y2 <= 0 or (equity_y3 <= 0):
                self.fundamentals['debtToEquityHistory'] = ([], [])
                w.append(Score.w_DE)
                p.append(Score.w_DE * Score.pf_mod)
                return Markup("⛔ D/E: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ D/E not calculated.")
            else:
                self.fundamentals['debtToEquityHistory'] = ([self.y3, self.y2, self.y1, self.y0, self.ttm], [dte_y3, dte_y2, dte_y1, dte_y0, dte_ttm])
                if (dte_ttm > 50 or dte_y0 > 50 or dte_y1 > 50 or (dte_y2 > 50) or (dte_y3 > 50)) and (dte_ttm < dte_y0 and dte_y0 < dte_y1 and (dte_y1 < dte_y2) and (dte_y2 < dte_y3)):
                    w.append(Score.w_DE)
                    p.append(Score.w_DE * Score.pf_mod)
                    w.append(Score.w_DE_decreasing)
                    p.append(Score.w_DE_decreasing * Score.pf_pos)
                    return Markup("⛔ D/E > 50%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(dte_y3) + '%, ' + str(dte_y2) + '%, ' + str(dte_y1) + '%, ' + str(dte_y0) + '%, ' + str(round(dte_ttm, 1)) + "%<br>↳ Solvency risk!<br>\t\t\t\t\t\t<span class='text-success'>↳ although: D/E consistently decreasing")
                elif (dte_ttm > 50 or dte_y0 > 50 or dte_y1 > 50 or (dte_y2 > 50) or (dte_y3 > 50)) and dte_ttm <= 50:
                    w.append(Score.w_DE)
                    p.append(Score.w_DE * Score.pf_mod)
                    return Markup("⛔ D/E > 50%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(dte_y3) + '%, ' + str(dte_y2) + '%, ' + str(dte_y1) + '%, ' + str(dte_y0) + '%, ' + str(round(dte_ttm, 1)) + "%<br>↳ Solvency risk!<br>\t\t\t\t\t\t<span class='text-success'>↳ although: D/E " + str(self.ttm) + ' ≤ 50% (' + str(dte_ttm) + '%)')
                elif dte_ttm > 50 or dte_y0 > 50 or dte_y1 > 50 or (dte_y2 > 50) or (dte_y3 > 50):
                    w.append(Score.w_DE)
                    p.append(Score.w_DE * Score.pf_neg)
                    return Markup("⛔ D/E > 50%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(dte_y3) + '%, ' + str(dte_y2) + '%, ' + str(dte_y1) + '%, ' + str(dte_y0) + '%, ' + str(round(dte_ttm, 1)) + '%<br>↳ Solvency risk!')
                elif (dte_ttm <= 50 and dte_y0 <= 50 and (dte_y1 <= 50) and (dte_y2 <= 50) and (dte_y3 <= 50)) and (dte_ttm > dte_y0 and dte_y0 > dte_y1 and (dte_y1 > dte_y2) and (dte_y2 > dte_y3)):
                    w.append(Score.w_DE)
                    p.append(Score.w_DE * Score.pf_pos)
                    w.append(Score.w_DE_increasing)
                    p.append(Score.w_DE_increasing * Score.pf_neg)
                    return Markup("✅ D/E ≤ 50%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(dte_y3) + '%, ' + str(dte_y2) + '%, ' + str(dte_y1) + '%, ' + str(dte_y0) + '%, ' + str(round(dte_ttm, 1)) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: D/E consistently increasing")
                elif dte_ttm <= 50 and dte_y0 <= 50 and (dte_y1 <= 50) and (dte_y2 <= 50) and (dte_y3 <= 50):
                    w.append(Score.w_DE)
                    p.append(Score.w_DE * Score.pf_pos)
                    return Markup("✅ D/E ≤ 50%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.ttm) + ': ' + str(dte_y3) + '%, ' + str(dte_y2) + '%, ' + str(dte_y1) + '%, ' + str(dte_y0) + '%, ' + str(round(dte_ttm, 1)) + '%')
        except:
            w.append(Score.w_DE)
            p.append(Score.w_DE * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about D/E!")

    def totalLiabilityToEquityHistory(self):
        """ TL/E: total liability/equity ≤ 0,8: consistent low total liability (if TL/E>1: company is using debt to finance its business!) """
        bs_t = self.bs_t
        w = self.weights_list
        p = self.points_list
        try:
            total_liabilities_y0 = self._cell(bs_t, 'Total Liab', 0)
            total_liabilities_y1 = self._cell(bs_t, 'Total Liab', 1)
            total_liabilities_y2 = self._cell(bs_t, 'Total Liab', 2)
            total_liabilities_y3 = self._cell(bs_t, 'Total Liab', 3)
            equity_y0 = self._cell(bs_t, 'Total Stockholder Equity', 0)
            equity_y1 = self._cell(bs_t, 'Total Stockholder Equity', 1)
            equity_y2 = self._cell(bs_t, 'Total Stockholder Equity', 2)
            equity_y3 = self._cell(bs_t, 'Total Stockholder Equity', 3)
            tlte_y0 = round(strict_divide(total_liabilities_y0, equity_y0) * 100, 2)
            tlte_y1 = round(strict_divide(total_liabilities_y1, equity_y1) * 100, 2)
            tlte_y2 = round(strict_divide(total_liabilities_y2, equity_y2) * 100, 2)
            tlte_y3 = round(strict_divide(total_liabilities_y3, equity_y3) * 100, 2)
            if equity_y0 <= 0 or equity_y1 <= 0 or equity_y2 <= 0 or (equity_y3 <= 0):
                self.fundamentals['totalLiabilityToEquityHistory'] = ([], [])
                w.append(Score.w_TLE)
                p.append(Score.w_TLE * Score.pf_mod)
                return Markup("⛔ TL/E: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ TL/E not calculated.")
            else:
                self.fundamentals['totalLiabilityToEquityHistory'] = ([self.y3, self.y2, self.y1, self.y0], [tlte_y3, tlte_y2, tlte_y1, tlte_y0])
                if (tlte_y0 > 100 or tlte_y1 > 100 or tlte_y2 > 100 or (tlte_y3 > 100)) and (tlte_y0 < tlte_y1 and tlte_y1 < tlte_y2 and (tlte_y2 < tlte_y3)):
                    w.append(Score.w_TLE)
                    p.append(Score.w_TLE * Score.pf_mod)
                    w.append(Score.w_TLE_decreasing)
                    p.append(Score.w_TLE_decreasing * Score.pf_pos)
                    return Markup("⛔ TL/E > 80%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(tlte_y3) + '%, ' + str(tlte_y2) + '%, ' + str(tlte_y1) + '%, ' + str(tlte_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ TL/E > 100%: Company uses debt to finance its business!<br>\t\t\t\t\t\t<span class='text-success'>↳ although: TL/E consistently decreasing")
                elif (tlte_y0 > 80 or tlte_y1 > 80 or tlte_y2 > 80 or (tlte_y3 > 80)) and (tlte_y0 < tlte_y1 and tlte_y1 < tlte_y2 and (tlte_y2 < tlte_y3)):
                    w.append(Score.w_TLE)
                    p.append(Score.w_TLE * Score.pf_mod)
                    return Markup("⛔ TL/E > 80%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(tlte_y3) + '%, ' + str(tlte_y2) + '%, ' + str(tlte_y1) + '%, ' + str(tlte_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: TL/E consistently decreasing")
                elif (tlte_y0 > 100 or tlte_y1 > 100 or tlte_y2 > 100 or (tlte_y3 > 100)) and tlte_y0 <= 80:
                    w.append(Score.w_TLE)
                    p.append(Score.w_TLE * Score.pf_mod)
                    return Markup("⛔ TL/E > 80%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(tlte_y3) + '%, ' + str(tlte_y2) + '%, ' + str(tlte_y1) + '%, ' + str(tlte_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ TL/E > 100%: Company uses debt to finance its business!<br>\t\t\t\t\t\t<span class='text-success'>↳ although: TL/E " + str(self.y0) + ' ≤ 80% (' + str(tlte_y0) + '%)')
                elif (tlte_y0 > 80 or tlte_y1 > 80 or tlte_y2 > 80 or (tlte_y3 > 80)) and tlte_y0 <= 80:
                    w.append(Score.w_TLE)
                    p.append(Score.w_TLE * Score.pf_mod)
                    return Markup("⛔ TL/E > 80%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(tlte_y3) + '%, ' + str(tlte_y2) + '%, ' + str(tlte_y1) + '%, ' + str(tlte_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ although: TL/E " + str(self.y0) + ' ≤ 80% (' + str(tlte_y0) + '%)')
                elif tlte_y0 > 100 or tlte_y1 > 100 or tlte_y2 > 100 or (tlte_y3 > 100):
                    w.append(Score.w_TLE)
                    p.append(Score.w_TLE * Score.pf_neg)
                    return Markup("⛔ TL/E > 80%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(tlte_y3) + '%, ' + str(tlte_y2) + '%, ' + str(tlte_y1) + '%, ' + str(tlte_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ TL/E > 100%: Company uses debt to finance its business!")
                elif tlte_y0 > 80 or tlte_y1 > 80 or tlte_y2 > 80 or (tlte_y3 > 80):
                    w.append(Score.w_TLE)
                    p.append(Score.w_TLE * Score.pf_neg)
                    return Markup("⛔ TL/E > 80%<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(tlte_y3) + '%, ' + str(tlte_y2) + '%, ' + str(tlte_y1) + '%, ' + str(tlte_y0) + '%')
                elif (tlte_y0 >= 0 and tlte_y0 <= 80 and (tlte_y1 >= 0) and (tlte_y1 <= 80) and (tlte_y2 >= 0) and (tlte_y2 <= 80) and (tlte_y3 >= 0) and (tlte_y3 <= 80)) and (tlte_y0 > tlte_y1 and tlte_y1 > tlte_y2 and (tlte_y2 > tlte_y3)):
                    w.append(Score.w_TLE)
                    p.append(Score.w_TLE * Score.pf_pos)
                    w.append(Score.w_TLE_increasing)
                    p.append(Score.w_TLE_increasing * Score.pf_neg)
                    return Markup("✅ TL/E ≤ 80%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(tlte_y3) + '%, ' + str(tlte_y2) + '%, ' + str(tlte_y1) + '%, ' + str(tlte_y0) + "%<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: TL/E consistently increasing")
                elif tlte_y0 >= 0 and tlte_y0 <= 80 and (tlte_y1 >= 0) and (tlte_y1 <= 80) and (tlte_y2 >= 0) and (tlte_y2 <= 80) and (tlte_y3 >= 0) and (tlte_y3 <= 80):
                    w.append(Score.w_TLE)
                    p.append(Score.w_TLE * Score.pf_pos)
                    return Markup("✅ TL/E ≤ 80%<br>\t\t\t\t\t\t<span class='text-success'>↳ " + str(self.y3) + '-' + str(self.y0) + ': ' + str(tlte_y3) + '%, ' + str(tlte_y2) + '%, ' + str(tlte_y1) + '%, ' + str(tlte_y0) + '%')
        except:
            w.append(Score.w_TLE)
            p.append(Score.w_TLE * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about TL/E!")

    def netBorrowingsHistory(self):
        """ Net Borrowings and NB/CFO: Te see how much FCF and FCFE change in time. No points. """
        data = self.data
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            net_borrowings_y0 = self._cell(cfs_t, 'Net Borrowings', 0)
            net_borrowings_y1 = self._cell(cfs_t, 'Net Borrowings', 1)
            net_borrowings_y2 = self._cell(cfs_t, 'Net Borrowings', 2)
            net_borrowings_y3 = self._cell(cfs_t, 'Net Borrowings', 3)
            cfo_y0 = self._cell(cfs_t, 'Total Cash From Operating Activities', 0)
            cfo_y1 = self._cell(cfs_t, 'Total Cash From Operating Activities', 1)
            cfo_y2 = self._cell(cfs_t, 'Total Cash From Operating Activities', 2)
            cfo_y3 = self._cell(cfs_t, 'Total Cash From Operating Activities', 3)
            net_borrowings_mln_y0 = '{:,}'.format(round(strict_divide(self._cell(cfs_t, 'Net Borrowings', 0), 1000000), 2))
            net_borrowings_mln_y1 = '{:,}'.format(round(strict_divide(self._cell(cfs_t, 'Net Borrowings', 1), 1000000), 2))
            net_borrowings_mln_y2 = '{:,}'.format(round(strict_divide(self._cell(cfs_t, 'Net Borrowings', 2), 1000000), 2))
            net_borrowings_mln_y3 = '{:,}'.format(round(strict_divide(self._cell(cfs_t, 'Net Borrowings', 3), 1000000), 2))
            net_borrowings_to_cfo_y0 = round(strict_divide(net_borrowings_y0, cfo_y0) * 100, 2)
            net_borrowings_to_cfo_y1 = round(strict_divide(net_borrowings_y1, cfo_y1) * 100, 2)
            net_borrowings_to_cfo_y2 = round(strict_divide(net_borrowings_y2, cfo_y2) * 100, 2)
            net_borrowings_to_cfo_y3 = round(strict_divide(net_borrowings_y3, cfo_y3) * 100, 2)
            if cfo_y0 <= 0 or cfo_y1 <= 0 or cfo_y2 <= 0 or (cfo_y3 <= 0):
                return Markup('ℹ Net Borrowings (NB):<br>↳ NB ' + str(self.y3) + '-' + str(self.y0) + ': ' + str(net_borrowings_mln_y3) + ', ' + str(net_borrowings_mln_y2) + ', ' + str(net_borrowings_mln_y1) + ', ' + str(net_borrowings_mln_y0) + ' mln ' + data['currency'] + '<br>↳ NB mean: ' + str(net_borrowings_mean) + ' mln ' + data['currency'] + "<br>↳ NB/CFO: Denominator ≤ 0 !<br>\t\t\t\t\t<span class='text-danger'>↳ NB/CFO not calculated.")
            else:
                net_borrowings_to_cfo_mean = round(strict_divide(net_borrowings_to_cfo_y0 + net_borrowings_to_cfo_y1 + net_borrowings_to_cfo_y2 + net_borrowings_to_cfo_y3, 4), 2)
                net_borrowings_mean = round(strict_divide(strict_divide(net_borrowings_y0 + net_borrowings_y1 + net_borrowings_y2 + net_borrowings_y3, 4), 1000000), 2)
                return Markup('ℹ Net Borrowings (NB):<br>↳ NB ' + str(self.y3) + '-' + str(self.y0) + ': ' + str(net_borrowings_mln_y3) + ', ' + str(net_borrowings_mln_y2) + ', ' + str(net_borrowings_mln_y1) + ', ' + str(net_borrowings_mln_y0) + ' mln ' + data['currency'] + '<br>↳ NB mean: ' + str(net_borrowings_mean) + ' mln ' + data['currency'] + '<br>↳ NB/CFO ' + str(self.y3) + '-' + str(self.y0) + ': ' + str(net_borrowings_to_cfo_y3) + '%, ' + str(net_borrowings_to_cfo_y2) + '%, ' + str(net_borrowings_to_cfo_y1) + '%, ' + str(net_borrowings_to_cfo_y0) + '%<br>↳ NB/CFO mean: ' + str(net_borrowings_to_cfo_mean))
        except:
            return Markup("❓ <span class='text-info'>No data about Net Borrowings to CFO (NB/CFO)!")

    def freeCashFlow(self):
        """ FCF (Free Cash Flow) = net income + depreciation + amortization - Capex = CFO - Capex: Consistent increasing FCF >7y """
        data = self.data
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            cfo_y0 = self._cell(cfs_t, 'Total Cash From Operating Activities', 0)
            cfo_y1 = self._cell(cfs_t, 'Total Cash From Operating Activities', 1)
            cfo_y2 = self._cell(cfs_t, 'Total Cash From Operating Activities', 2)
            cfo_y3 = self._cell(cfs_t, 'Total Cash From Operating Activities', 3)
            capex_y0 = -self._cell(cfs_t, 'Capital Expenditures', 0)
            capex_y1 = -self._cell(cfs_t, 'Capital Expenditures', 1)
            capex_y2 = -self._cell(cfs_t, 'Capital Expenditures', 2)
            capex_y3 = -self._cell(cfs_t, 'Capital Expenditures', 3)
            fcf_y0 = round(strict_divide(cfo_y0 - capex_y0, 1000000), 2)
            fcf_y1 = round(strict_divide(cfo_y1 - capex_y1, 1000000), 2)
            fcf_y2 = round(strict_divide(cfo_y2 - capex_y2, 1000000), 2)
            fcf_y3 = round(strict_divide(cfo_y3 - capex_y3, 1000000), 2)
            self.fundamentals['freeCashFlow'] = ([self.y3, self.y2, self.y1, self.y0], [fcf_y3, fcf_y2, fcf_y1, fcf_y0])
            if pd.isna(fcf_y0) == True or pd.isna(fcf_y1) == True or pd.isna(fcf_y2) == True or (pd.isna(fcf_y3) == True):
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_mod)
                return Markup("❓ <span class='text-info'>No data about Free Cash Flow (FCF)!")
            elif (fcf_y0 == 0 or fcf_y1 == 0 or fcf_y2 == 0 or (fcf_y3 == 0)) and (fcf_y0 > 0 or fcf_y1 > 0 or fcf_y2 > 0 or (fcf_y3 > 0)) and (fcf_y0 < 0 or fcf_y1 < 0 or fcf_y2 < 0 or (fcf_y3 < 0)):
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_mod)
                return Markup("⛔ Free Cash Flow (FCF) alternating POSITIVE, NEGATIVE and ZERO!<br>\t\t\t\t\t<span class='text-danger'>↳ FCF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcf_y3) + ', ' + str(fcf_y2) + ', ' + str(fcf_y1) + ', ' + str(fcf_y0) + ' mln ' + data['currency'])
            elif (fcf_y0 == 0 or fcf_y1 == 0 or fcf_y2 == 0 or (fcf_y3 == 0)) and (fcf_y0 > 0 or fcf_y1 > 0 or fcf_y2 > 0 or (fcf_y3 > 0)):
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_mod)
                return Markup("⛔ Free Cash Flow (FCF) alternating POSITIVE and ZERO!<br>\t\t\t\t\t<span class='text-danger'>↳ FCF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcf_y3) + ', ' + str(fcf_y2) + ', ' + str(fcf_y1) + ', ' + str(fcf_y0) + ' mln ' + data['currency'])
            elif (fcf_y0 == 0 or fcf_y1 == 0 or fcf_y2 == 0 or (fcf_y3 == 0)) and (fcf_y0 < 0 or fcf_y1 < 0 or fcf_y2 < 0 or (fcf_y3 < 0)):
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_neg)
                return Markup("⛔ Free Cash Flow (FCF) alternating NEGATIVE and ZERO!<br>\t\t\t\t\t<span class='text-danger'>↳ FCF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcf_y3) + ', ' + str(fcf_y2) + ', ' + str(fcf_y1) + ', ' + str(fcf_y0) + ' mln ' + data['currency'])
            elif fcf_y0 == 0 and fcf_y1 == 0 and (fcf_y2 == 0) and (fcf_y3 == 0):
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_neg)
                return Markup('⛔ Free Cash Flow (FCF) consistently ZERO!')
            elif (fcf_y0 > 0 or fcf_y1 > 0 or fcf_y2 > 0 or (fcf_y3 > 0)) and (fcf_y0 < 0 or fcf_y1 < 0 or fcf_y2 < 0 or (fcf_y3 < 0)):
                return Markup("⛔ Free Cash Flow (FCF) alternating POSITIVE and NEGATIVE!<br>\t\t\t\t\t<span class='text-danger'>↳ FCF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcf_y3) + ', ' + str(fcf_y2) + ', ' + str(fcf_y1) + ', ' + str(fcf_y0) + ' mln ' + data['currency'])
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_mod)
            elif fcf_y0 < 0 and fcf_y1 < 0 and (fcf_y2 < 0) and (fcf_y3 < 0):
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_neg)
                return Markup("⛔ Free Cash Flow (FCF) consistently NEGATIVE!<br>\t\t\t\t\t<span class='text-danger'>↳ FCF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcf_y3) + ', ' + str(fcf_y2) + ', ' + str(fcf_y1) + ', ' + str(fcf_y0) + ' mln ' + data['currency'])
            elif (fcf_y0 > 0 and fcf_y1 > 0 and (fcf_y2 > 0) and (fcf_y3 > 0)) and (fcf_y0 < fcf_y1 and fcf_y1 < fcf_y2 and (fcf_y2 < fcf_y3)):
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_pos)
                w.append(Score.w_FCF_decreasing)
                p.append(Score.w_FCF_decreasing * Score.pf_neg)
                return Markup("✅ Free Cash Flow (FCF) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcf_y3) + ', ' + str(fcf_y2) + ', ' + str(fcf_y1) + ', ' + str(fcf_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ CAVE: Free Cash Flow (FCF) consistently decreasing!")
            elif (fcf_y0 > 0 and fcf_y1 > 0 and (fcf_y2 > 0) and (fcf_y3 > 0)) and (fcf_y0 < fcf_y1 or fcf_y1 < fcf_y2 or fcf_y2 < fcf_y3) and (fcf_y0 > fcf_y3):
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_pos)
                w.append(Score.w_FCF_increasing)
                p.append(Score.w_FCF_increasing * Score.pf_mod)
                return Markup("✅ Free Cash Flow (FCF) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcf_y3) + ', ' + str(fcf_y2) + ', ' + str(fcf_y1) + ', ' + str(fcf_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ CAVE: FCF not consistently increasing!<br>\t\t\t\t\t<span class='text-success'>↳ although: FCF " + str(self.y3) + ' < ' + str(self.y0) + ' (' + str(fcf_y3) + ' < ' + str(fcf_y0) + ' mln ' + data['currency'] + ')')
            elif (fcf_y0 > 0 and fcf_y1 > 0 and (fcf_y2 > 0) and (fcf_y3 > 0)) and (fcf_y0 < fcf_y1 or fcf_y1 < fcf_y2 or fcf_y2 < fcf_y3):
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_pos)
                w.append(Score.w_FCF_increasing)
                p.append(Score.w_FCF_increasing * Score.pf_neg)
                return Markup("✅ Free Cash Flow (FCF) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcf_y3) + ', ' + str(fcf_y2) + ', ' + str(fcf_y1) + ', ' + str(fcf_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ CAVE: FCF not consistently increasing!")
            elif (fcf_y0 > 0 and fcf_y1 > 0 and (fcf_y2 > 0) and (fcf_y3 > 0)) and (fcf_y0 > fcf_y1 and fcf_y1 > fcf_y2 and (fcf_y2 > fcf_y3)):
                w.append(Score.w_FCF)
                p.append(Score.w_FCF * Score.pf_pos)
                w.append(Score.w_FCF_increasing)
                p.append(Score.w_FCF_increasing * Score.pf_pos)
                return Markup("✅ Free Cash Flow (FCF) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcf_y3) + ', ' + str(fcf_y2) + ', ' + str(fcf_y1) + ', ' + str(fcf_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-success'>↳ Free Cash Flow (FCF) consistently increasing!")
        except:
            w.append(Score.w_FCF)
            p.append(Score.w_FCF * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Free Cash Flow (FCF)!")

    def freeCashFlowCAGR(self):
        """ FCF (Free Cash Flow) CAGR """
        data = self.data
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            cfo_y0 = self._cell(cfs_t, 'Total Cash From Operating Activities', 0)
            cfo_y3 = self._cell(cfs_t, 'Total Cash From Operating Activities', 3)
            capex_y0 = -self._cell(cfs_t, 'Capital Expenditures', 0)
            capex_y3 = -self._cell(cfs_t, 'Capital Expenditures', 3)
            fcf_y0 = round(strict_divide(cfo_y0 - capex_y0, 1000000), 2)
            fcf_y3 = round(strict_divide(cfo_y3 - capex_y3, 1000000), 2)
            if pd.isna(fcf_y0) == True or pd.isna(fcf_y3) == True:
                w.append(Score.w_FCF_growth_2000bp)
                p.append(Score.w_FCF_growth_2000bp * Score.pf_mod)
                return Markup("<br>❓ <span class='text-info'>No data about Free Cash Flow (FCF) CAGR!")
            elif fcf_y0 <= 0 and fcf_y3 <= 0:
                self.fundamentals['freeCashFlowCAGR'] = 'NaN'
                w.append(Score.w_FCF_growth_2000bp)
                p.append(Score.w_FCF_growth_2000bp * Score.pf_neg)
                return Markup("<br><span class='text-danger'>↳ FCF ≤ 0: FCF CAGR(3y): NaN")
            else:
                fcf_cagr_prior3y = round((strict_divide(fcf_y0, fcf_y3) ** strict_divide(1, 3) - 1) * 100, 2)
                self.fundamentals['freeCashFlowCAGR'] = fcf_cagr_prior3y
                if fcf_cagr_prior3y >= 20:
                    w.append(Score.w_FCF_growth_2000bp)
                    p.append(Score.w_FCF_growth_2000bp * Score.pf_pos)
                    return Markup("<br>\t\t\t\t\t\t<span class='text-success'>↳ FCF CAGR(3y) ≥ 20% : " + str(fcf_cagr_prior3y) + '% per year!')
                elif fcf_cagr_prior3y > 0 and fcf_cagr_prior3y < 20:
                    w.append(Score.w_FCF_growth_2000bp)
                    p.append(Score.w_FCF_growth_2000bp * Score.pf_mod)
                    return Markup("<br>\t\t\t\t\t\t<span class='text-danger'>↳ FCF CAGR(3y) < 20% : " + str(fcf_cagr_prior3y) + '% per year!')
                elif fcf_cagr_prior3y <= 0:
                    w.append(Score.w_FCF_growth_2000bp)
                    p.append(Score.w_FCF_growth_2000bp * Score.pf_neg)
                    return Markup("<br>\t\t\t\t\t\t<span class='text-danger'>↳ FCF CAGR(3y) NEGATIVE: " + str(fcf_cagr_prior3y) + '% per year!')
        except:
            w.append(Score.w_FCF_growth_2000bp)
            p.append(Score.w_FCF_growth_2000bp * Score.pf_mod)
            return Markup("<br>❓ <span class='text-info'>No data about Free Cash Flow (FCF) CAGR!")

    def freeCashFlowToFirm(self):
        """ FCFF (Free Cash Flow to Firm) = UFCF  = CFO - CapEx + I*(1-Tax) = FCF + I*(1-Tax): Consistent increasing FCFF >7y """
        data = self.data
        pal_t = self.pal_t
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            cfo_y0 = self._cell(cfs_t, 'Total Cash From Operating Activities', 0)
            cfo_y1 = self._cell(cfs_t, 'Total Cash From Operating Activities', 1)
            cfo_y2 = self._cell(cfs_t, 'Total Cash From Operating Activities', 2)
            cfo_y3 = self._cell(cfs_t, 'Total Cash From Operating Activities', 3)
            capex_y0 = -self._cell(cfs_t, 'Capital Expenditures', 0)
            capex_y1 = -self._cell(cfs_t, 'Capital Expenditures', 1)
            capex_y2 = -self._cell(cfs_t, 'Capital Expenditures', 2)
            capex_y3 = -self._cell(cfs_t, 'Capital Expenditures', 3)
            interest_expense_y0 = -self._cell(pal_t, 'Interest Expense', 0)
            interest_expense_y1 = -self._cell(pal_t, 'Interest Expense', 1)
            interest_expense_y2 = -self._cell(pal_t, 'Interest Expense', 2)
            interest_expense_y3 = -self._cell(pal_t, 'Interest Expense', 3)
            income_tax_expense_y0 = self._cell(pal_t, 'Income Tax Expense', 0)
            income_tax_expense_y1 = self._cell(pal_t, 'Income Tax Expense', 1)
            income_tax_expense_y2 = self._cell(pal_t, 'Income Tax Expense', 2)
            income_tax_expense_y3 = self._cell(pal_t, 'Income Tax Expense', 3)
            ebt_y0 = self._cell(pal_t, 'Income Before Tax', 0)
            ebt_y1 = self._cell(pal_t, 'Income Before Tax', 1)
            ebt_y2 = self._cell(pal_t, 'Income Before Tax', 2)
            ebt_y3 = self._cell(pal_t, 'Income Before Tax', 3)
            tax_rate_y0 = strict_divide(income_tax_expense_y0, ebt_y0)
            tax_rate_y1 = strict_divide(income_tax_expense_y0, ebt_y1)
            tax_rate_y2 = strict_divide(income_tax_expense_y0, ebt_y2)
            tax_rate_y3 = strict_divide(income_tax_expense_y0, ebt_y3)
            fcff_y0 = round(strict_divide(cfo_y0 - capex_y0 + interest_expense_y0 * (1 - tax_rate_y0), 1000000), 2)
            fcff_y1 = round(strict_divide(cfo_y1 - capex_y1 + interest_expense_y1 * (1 - tax_rate_y1), 1000000), 2)
            fcff_y2 = round(strict_divide(cfo_y2 - capex_y2 + interest_expense_y2 * (1 - tax_rate_y2), 1000000), 2)
            fcff_y3 = round(strict_divide(cfo_y3 - capex_y3 + interest_expense_y3 * (1 - tax_rate_y3), 1000000), 2)
            self.fundamentals['freeCashFlowToFirm'] = ([self.y3, self.y2, self.y1, self.y0], [fcff_y3, fcff_y2, fcff_y1, fcff_y0])
            if pd.isna(fcff_y0) == True or pd.isna(fcff_y1) == True or pd.isna(fcff_y2) == True or (pd.isna(fcff_y3) == True):
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_mod)
                return Markup("❓ <span class='text-info'>No data about Free Cash Flow to Firm (FCFF)!")
            elif (fcff_y0 == 0 or fcff_y1 == 0 or fcff_y2 == 0 or (fcff_y3 == 0)) and (fcff_y0 > 0 or fcff_y1 > 0 or fcff_y2 > 0 or (fcff_y3 > 0)) and (fcff_y0 < 0 or fcff_y1 < 0 or fcff_y2 < 0 or (fcff_y3 < 0)):
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_mod)
                return Markup("⛔ Free Cash Flow to Firm (FCFF) alternating POSITIVE, NEGATIVE and ZERO!<br>\t\t\t\t\t<span class='text-danger'>↳ FCFF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcff_y3) + ', ' + str(fcff_y2) + ', ' + str(fcff_y1) + ', ' + str(fcff_y0) + ' mln ' + data['currency'])
            elif (fcff_y0 == 0 or fcff_y1 == 0 or fcff_y2 == 0 or (fcff_y3 == 0)) and (fcff_y0 > 0 or fcff_y1 > 0 or fcff_y2 > 0 or (fcff_y3 > 0)):
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_mod)
                return Markup("⛔ Free Cash Flow to Firm (FCFF) alternating POSITIVE and ZERO!<br>\t\t\t\t\t<span class='text-danger'>↳ FCFF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcff_y3) + ', ' + str(fcff_y2) + ', ' + str(fcff_y1) + ', ' + str(fcff_y0) + ' mln ' + data['currency'])
            elif (fcff_y0 == 0 or fcff_y1 == 0 or fcff_y2 == 0 or (fcff_y3 == 0)) and (fcff_y0 < 0 or fcff_y1 < 0 or fcff_y2 < 0 or (fcff_y3 < 0)):
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_neg)
                return Markup("⛔ Free Cash Flow to Firm (FCFF) alternating NEGATIVE and ZERO!<br>\t\t\t\t\t<span class='text-danger'>↳ FCFF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcff_y3) + ', ' + str(fcff_y2) + ', ' + str(fcff_y1) + ', ' + str(fcff_y0) + ' mln ' + data['currency'])
            elif fcff_y0 == 0 and fcff_y1 == 0 and (fcff_y2 == 0) and (fcff_y3 == 0):
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_neg)
                return Markup('⛔ Free Cash Flow to Firm (FCFF) consistently ZERO!')
            elif (fcff_y0 > 0 or fcff_y1 > 0 or fcff_y2 > 0 or (fcff_y3 > 0)) and (fcff_y0 < 0 or fcff_y1 < 0 or fcff_y2 < 0 or (fcff_y3 < 0)):
                return Markup("⛔ Free Cash Flow to Firm (FCFF) alternating POSITIVE and NEGATIVE!<br>\t\t\t\t\t<span class='text-danger'>↳ FCFF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcff_y3) + ', ' + str(fcff_y2) + ', ' + str(fcff_y1) + ', ' + str(fcff_y0) + ' mln ' + data['currency'])
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_mod)
            elif fcff_y0 < 0 and fcff_y1 < 0 and (fcff_y2 < 0) and (fcff_y3 < 0):
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_neg)
                return Markup("⛔ Free Cash Flow to Firm (FCFF) consistently NEGATIVE!<br>\t\t\t\t\t<span class='text-danger'>↳ FCFF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcff_y3) + ', ' + str(fcff_y2) + ', ' + str(fcff_y1) + ', ' + str(fcff_y0) + ' mln ' + data['currency'])
            elif (fcff_y0 > 0 and fcff_y1 > 0 and (fcff_y2 > 0) and (fcff_y3 > 0)) and (fcff_y0 < fcff_y1 and fcff_y1 < fcff_y2 and (fcff_y2 < fcff_y3)):
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_pos)
                w.append(Score.w_FCFF_decreasing)
                p.append(Score.w_FCFF_decreasing * Score.pf_neg)
                return Markup("✅ Free Cash Flow to Firm (FCFF) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCFF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcff_y3) + ', ' + str(fcff_y2) + ', ' + str(fcff_y1) + ', ' + str(fcff_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ CAVE: Free Cash Flow to Firm (FCFF) consistently decreasing!")
            elif (fcff_y0 > 0 and fcff_y1 > 0 and (fcff_y2 > 0) and (fcff_y3 > 0)) and (fcff_y0 < fcff_y1 or fcff_y1 < fcff_y2 or fcff_y2 < fcff_y3) and (fcff_y0 > fcff_y3):
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_pos)
                w.append(Score.w_FCFF_increasing)
                p.append(Score.w_FCFF_increasing * Score.pf_mod)
                return Markup("✅ Free Cash Flow to Firm (FCFF) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCFF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcff_y3) + ', ' + str(fcff_y2) + ', ' + str(fcff_y1) + ', ' + str(fcff_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ CAVE: FCFF not consistently increasing!<br>\t\t\t\t\t<span class='text-success'>↳ although: FCFF " + str(self.y3) + ' < ' + str(self.y0) + ' (' + str(fcff_y3) + ' < ' + str(fcff_y0) + ' mln ' + data['currency'] + ')')
            elif (fcff_y0 > 0 and fcff_y1 > 0 and (fcff_y2 > 0) and (fcff_y3 > 0)) and (fcff_y0 < fcff_y1 or fcff_y1 < fcff_y2 or fcff_y2 < fcff_y3):
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_pos)
                w.append(Score.w_FCFF_increasing)
                p.append(Score.w_FCFF_increasing * Score.pf_neg)
                return Markup("✅ Free Cash Flow to Firm (FCFF) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCFF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcff_y3) + ', ' + str(fcff_y2) + ', ' + str(fcff_y1) + ', ' + str(fcff_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ CAVE: FCFF not consistently increasing!")
            elif (fcff_y0 > 0 and fcff_y1 > 0 and (fcff_y2 > 0) and (fcff_y3 > 0)) and (fcff_y0 > fcff_y1 and fcff_y1 > fcff_y2 and (fcff_y2 > fcff_y3)):
                w.append(Score.w_FCFF)
                p.append(Score.w_FCFF * Score.pf_pos)
                w.append(Score.w_FCFF_increasing)
                p.append(Score.w_FCFF_increasing * Score.pf_pos)
                return Markup("✅ Free Cash Flow to Firm (FCFF) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCFF " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcff_y3) + ', ' + str(fcff_y2) + ', ' + str(fcff_y1) + ', ' + str(fcff_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-success'>↳ Free Cash Flow to Firm (FCFF) consistently increasing!")
        except:
            w.append(Score.w_FCFF)
            p.append(Score.w_FCFF * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Free Cash Flow to Firm (FCFF)!")

    def freeCashFlowToFirmCAGR(self):
        """ FCF (Free Cash Flow) CAGR """
        data = self.data
        pal_t = self.pal_t
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            cfo_y0 = self._cell(cfs_t, 'Total Cash From Operating Activities', 0)
            cfo_y3 = self._cell(cfs_t, 'Total Cash From Operating Activities', 3)
            capex_y0 = -self._cell(cfs_t, 'Capital Expenditures', 0)
            capex_y3 = -self._cell(cfs_t, 'Capital Expenditures', 3)
            interest_expense_y0 = -self._cell(pal_t, 'Interest Expense', 0)
            interest_expense_y3 = -self._cell(pal_t, 'Interest Expense', 3)
            income_tax_expense_y0 = self._cell(pal_t, 'Income Tax Expense', 0)
            income_tax_expense_y3 = self._cell(pal_t, 'Income Tax Expense', 3)
            ebt_y0 = self._cell(pal_t, 'Income Before Tax', 0)
            ebt_y3 = self._cell(pal_t, 'Income Before Tax', 3)
            tax_rate_y0 = strict_divide(income_tax_expense_y0, ebt_y0)
            tax_rate_y3 = strict_divide(income_tax_expense_y0, ebt_y3)
            fcff_y0 = round(strict_divide(cfo_y0 - capex_y0 + interest_expense_y0 * (1 - tax_rate_y0), 1000000), 2)
            fcff_y3 = round(strict_divide(cfo_y3 - capex_y3 + interest_expense_y3 * (1 - tax_rate_y3), 1000000), 2)
            if pd.isna(fcff_y0) == True or pd.isna(fcff_y3) == True:
                w.append(Score.w_FCFF_growth_2000bp)
                p.append(Score.w_FCFF_growth_2000bp * Score.pf_mod)
                return Markup("<br>❓ <span class='text-info'>No data about Free Cash Flow to Firm (FCFF) CAGR!")
            elif fcff_y0 <= 0 and fcff_y3 <= 0:
                self.fundamentals['freeCashFlowToFirmCAGR'] = 'NaN'
                w.append(Score.w_FCFF_growth_2000bp)
                p.append(Score.w_FCFF_growth_2000bp * Score.pf_neg)
                return Markup("<br><span class='text-danger'>↳ FCFF ≤ 0: FCFF CAGR(3y): NaN")
            else:
                fcff_cagr_prior3y = round((strict_divide(fcff_y0, fcff_y3) ** strict_divide(1, 3) - 1) * 100, 2)
                self.fundamentals['freeCashFlowToFirmCAGR'] = fcff_cagr_prior3y
                if fcff_cagr_prior3y >= 20:
                    w.append(Score.w_FCFF_growth_2000bp)
                    p.append(Score.w_FCFF_growth_2000bp * Score.pf_pos)
                    return Markup("<br>\t\t\t\t\t\t<span class='text-success'>↳ FCFF CAGR(3y) ≥ 20% : " + str(fcff_cagr_prior3y) + '% per year!')
                elif fcff_cagr_prior3y > 0 and fcff_cagr_prior3y < 20:
                    w.append(Score.w_FCFF_growth_2000bp)
                    p.append(Score.w_FCFF_growth_2000bp * Score.pf_mod)
                    return Markup("<br>\t\t\t\t\t\t<span class='text-danger'>↳ FCFF CAGR(3y) < 20% : " + str(fcff_cagr_prior3y) + '% per year!')
                elif fcff_cagr_prior3y <= 0:
                    w.append(Score.w_FCFF_growth_2000bp)
                    p.append(Score.w_FCFF_growth_2000bp * Score.pf_neg)
                    return Markup("<br>\t\t\t\t\t\t<span class='text-danger'>↳ FCFF CAGR(3y) NEGATIVE: " + str(fcff_cagr_prior3y) + '% per year!')
        except:
            w.append(Score.w_FCFF_growth_2000bp)
            p.append(Score.w_FCFF_growth_2000bp * Score.pf_mod)
            return Markup("<br>❓ <span class='text-info'>No data about Free Cash Flow to Firm (FCFF) CAGR!")

    def freeCashFlowToEquity(self):
        """" FCFE (Free Cash Flow to Equity) = LFCF = CFO - CapEx + Net Borrowings = FCF + Net Borrowings: Consistent increasing FCFE >7y """
        data = self.data
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            cfo_y0 = self._cell(cfs_t, 'Total Cash From Operating Activities', 0)
            cfo_y1 = self._cell(cfs_t, 'Total Cash From Operating Activities', 1)
            cfo_y2 = self._cell(cfs_t, 'Total Cash From Operating Activities', 2)
            cfo_y3 = self._cell(cfs_t, 'Total Cash From Operating Activities', 3)
            capex_y0 = -self._cell(cfs_t, 'Capital Expenditures', 0)
            capex_y1 = -self._cell(cfs_t, 'Capital Expenditures', 1)
            capex_y2 = -self._cell(cfs_t, 'Capital Expenditures', 2)
            capex_y3 = -self._cell(cfs_t, 'Capital Expenditures', 3)
            net_borrowings_y0 = self._cell(cfs_t, 'Net Borrowings', 0)
            net_borrowings_y1 = self._cell(cfs_t, 'Net Borrowings', 1)
            net_borrowings_y2 = self._cell(cfs_t, 'Net Borrowings', 2)
            net_borrowings_y3 = self._cell(cfs_t, 'Net Borrowings', 3)
            fcfe_y0 = round(strict_divide(cfo_y0 - capex_y0 + net_borrowings_y0, 1000000), 2)
            fcfe_y1 = round(strict_divide(cfo_y1 - capex_y1 + net_borrowings_y1, 1000000), 2)
            fcfe_y2 = round(strict_divide(cfo_y2 - capex_y2 + net_borrowings_y2, 1000000), 2)
            fcfe_y3 = round(strict_divide(cfo_y3 - capex_y3 + net_borrowings_y3, 1000000), 2)
            self.fundamentals['freeCashFlowToEquity'] = ([self.y3, self.y2, self.y1, self.y0], [fcfe_y3, fcfe_y2, fcfe_y1, fcfe_y0])
            if pd.isna(fcfe_y0) == True or pd.isna(fcfe_y1) == True or pd.isna(fcfe_y2) == True or (pd.isna(fcfe_y3) == True):
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_mod)
                return Markup("❓ <span class='text-info'>No data about Free Cash Flow to Equity (FCFE)!")
            elif (fcfe_y0 == 0 or fcfe_y1 == 0 or fcfe_y2 == 0 or (fcfe_y3 == 0)) and (fcfe_y0 > 0 or fcfe_y1 > 0 or fcfe_y2 > 0 or (fcfe_y3 > 0)) and (fcfe_y0 < 0 or fcfe_y1 < 0 or fcfe_y2 < 0 or (fcfe_y3 < 0)):
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_mod)
                return Markup("⛔ Free Cash Flow to Equity (FCFE) alternating POSITIVE, NEGATIVE and ZERO!<br>\t\t\t\t\t<span class='text-danger'>↳ FCFE " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcfe_y3) + ', ' + str(fcfe_y2) + ', ' + str(fcfe_y1) + ', ' + str(fcfe_y0) + ' mln ' + data['currency'])
            elif (fcfe_y0 == 0 or fcfe_y1 == 0 or fcfe_y2 == 0 or (fcfe_y3 == 0)) and (fcfe_y0 > 0 or fcfe_y1 > 0 or fcfe_y2 > 0 or (fcfe_y3 > 0)):
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_mod)
                return Markup("⛔ Free Cash Flow to Equity (FCFE) alternating POSITIVE and ZERO!<br>\t\t\t\t\t<span class='text-danger'>↳ FCFE " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcfe_y3) + ', ' + str(fcfe_y2) + ', ' + str(fcfe_y1) + ', ' + str(fcfe_y0) + ' mln ' + data['currency'])
            elif (fcfe_y0 == 0 or fcfe_y1 == 0 or fcfe_y2 == 0 or (fcfe_y3 == 0)) and (fcfe_y0 < 0 or fcfe_y1 < 0 or fcfe_y2 < 0 or (fcfe_y3 < 0)):
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_neg)
                return Markup("⛔ Free Cash Flow to Equity (FCFE) alternating NEGATIVE and ZERO!<br>\t\t\t\t\t<span class='text-danger'>↳ FCFE " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcfe_y3) + ', ' + str(fcfe_y2) + ', ' + str(fcfe_y1) + ', ' + str(fcfe_y0) + ' mln ' + data['currency'])
            elif fcfe_y0 == 0 and fcfe_y1 == 0 and (fcfe_y2 == 0) and (fcfe_y3 == 0):
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_neg)
                return Markup('⛔ Free Cash Flow to Equity (FCFE) consistently ZERO!')
            elif (fcfe_y0 > 0 or fcfe_y1 > 0 or fcfe_y2 > 0 or (fcfe_y3 > 0)) and (fcfe_y0 < 0 or fcfe_y1 < 0 or fcfe_y2 < 0 or (fcfe_y3 < 0)):
                return Markup("⛔ Free Cash Flow to Equity (FCFE) alternating POSITIVE and NEGATIVE!<br>\t\t\t\t\t<span class='text-danger'>↳ FCFE " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcfe_y3) + ', ' + str(fcfe_y2) + ', ' + str(fcfe_y1) + ', ' + str(fcfe_y0) + ' mln ' + data['currency'])
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_mod)
            elif fcfe_y0 < 0 and fcfe_y1 < 0 and (fcfe_y2 < 0) and (fcfe_y3 < 0):
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_neg)
                return Markup("⛔ Free Cash Flow to Equity (FCFE) consistently NEGATIVE!<br>\t\t\t\t\t<span class='text-danger'>↳ FCFE " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcfe_y3) + ', ' + str(fcfe_y2) + ', ' + str(fcfe_y1) + ', ' + str(fcfe_y0) + ' mln ' + data['currency'])
            elif (fcfe_y0 > 0 and fcfe_y1 > 0 and (fcfe_y2 > 0) and (fcfe_y3 > 0)) and (fcfe_y0 < fcfe_y1 and fcfe_y1 < fcfe_y2 and (fcfe_y2 < fcfe_y3)):
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_pos)
                w.append(Score.w_FCFE_decreasing)
                p.append(Score.w_FCFE_decreasing * Score.pf_neg)
                return Markup("✅ Free Cash Flow to Equity (FCFE) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCFE " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcfe_y3) + ', ' + str(fcfe_y2) + ', ' + str(fcfe_y1) + ', ' + str(fcfe_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ CAVE: Free Cash Flow to Equity (FCFE) consistently decreasing!")
            elif (fcfe_y0 > 0 and fcfe_y1 > 0 and (fcfe_y2 > 0) and (fcfe_y3 > 0)) and (fcfe_y0 < fcfe_y1 or fcfe_y1 < fcfe_y2 or fcfe_y2 < fcfe_y3) and (fcfe_y0 > fcfe_y3):
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_pos)
                w.append(Score.w_FCFE_increasing)
                p.append(Score.w_FCFE_increasing * Score.pf_mod)
                return Markup("✅ Free Cash Flow to Equity (FCFE) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCFE " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcfe_y3) + ', ' + str(fcfe_y2) + ', ' + str(fcfe_y1) + ', ' + str(fcfe_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ CAVE: FCFE not consistently increasing!<br>\t\t\t\t\t<span class='text-success'>↳ although: FCFE " + str(self.y3) + ' < ' + str(self.y0) + ' (' + str(fcfe_y3) + ' < ' + str(fcfe_y0) + ' mln ' + data['currency'] + ')')
            elif (fcfe_y0 > 0 and fcfe_y1 > 0 and (fcfe_y2 > 0) and (fcfe_y3 > 0)) and (fcfe_y0 < fcfe_y1 or fcfe_y1 < fcfe_y2 or fcfe_y2 < fcfe_y3):
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_pos)
                w.append(Score.w_FCFE_increasing)
                p.append(Score.w_FCFE_increasing * Score.pf_neg)
                return Markup("✅ Free Cash Flow to Equity (FCFE) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCFE " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcfe_y3) + ', ' + str(fcfe_y2) + ', ' + str(fcfe_y1) + ', ' + str(fcfe_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-danger'>↳ CAVE: FCFE not consistently increasing!")
            elif (fcfe_y0 > 0 and fcfe_y1 > 0 and (fcfe_y2 > 0) and (fcfe_y3 > 0)) and (fcfe_y0 > fcfe_y1 and fcfe_y1 > fcfe_y2 and (fcfe_y2 > fcfe_y3)):
                w.append(Score.w_FCFE)
                p.append(Score.w_FCFE * Score.pf_pos)
                w.append(Score.w_FCFE_increasing)
                p.append(Score.w_FCFE_increasing * Score.pf_pos)
                return Markup("✅ Free Cash Flow to Equity (FCFE) consistently POSITIVE!<br>\t\t\t\t\t<span class='text-success'>↳ FCFE " + str(self.y3) + '-' + str(self.y0) + ': ' + str(fcfe_y3) + ', ' + str(fcfe_y2) + ', ' + str(fcfe_y1) + ', ' + str(fcfe_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t<span class='text-success'>↳ Free Cash Flow to Equity (FCFE) consistently increasing!")
        except:
            w.append(Score.w_FCFE)
            p.append(Score.w_FCFE * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Free Cash Flow to Equity (FCFE)!")

    def freeCashFlowToEquityCAGR(self):
        """" FCFE (Free Cash Flow to Equity) = FCF + Net Borrowings: Consistent increasing FCFE >7y """
        data = self.data
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            cfo_y0 = self._cell(cfs_t, 'Total Cash From Operating Activities', 0)
            cfo_y3 = self._cell(cfs_t, 'Total Cash From Operating Activities', 3)
            capex_y0 = -self._cell(cfs_t, 'Capital Expenditures', 0)
            capex_y3 = -self._cell(cfs_t, 'Capital Expenditures', 3)
            net_borrowings_y0 = self._cell(cfs_t, 'Net Borrowings', 0)
            net_borrowings_y3 = self._cell(cfs_t, 'Net Borrowings', 3)
            fcfe_y0 = round(strict_divide(cfo_y0 - capex_y0 + net_borrowings_y0, 1000000), 2)
            fcfe_y3 = round(strict_divide(cfo_y3 - capex_y3 + net_borrowings_y3, 1000000), 2)
            if pd.isna(fcfe_y0) == True or pd.isna(fcfe_y3) == True:
                w.append(Score.w_FCFE_growth_2000bp)
                p.append(Score.w_FCFE_growth_2000bp * Score.pf_mod)
                return Markup("<br>❓ <span class='text-info'>No data about Free Cash Flow to Equity (FCFE) CAGR!")
            elif fcfe_y0 <= 0 and fcfe_y3 <= 0:
                self.fundamentals['freeCashFlowToEquityCAGR'] = 'NaN'
                w.append(Score.w_FCFE_growth_2000bp)
                p.append(Score.w_FCFE_growth_2000bp * Score.pf_neg)
                return Markup("<br><span class='text-danger'>↳ FCFE ≤ 0: FCFE CAGR(3y): NaN")
            else:
                fcfe_cagr_prior3y = round((strict_divide(fcfe_y0, fcfe_y3) ** strict_divide(1, 3) - 1) * 100, 2)
                self.fundamentals['freeCashFlowToEquityCAGR'] = fcfe_cagr_prior3y
                if fcfe_cagr_prior3y >= 20:
                    w.append(Score.w_FCFE_growth_2000bp)
                    p.append(Score.w_FCFE_growth_2000bp * Score.pf_pos)
                    return Markup("<br>\t\t\t\t\t\t<span class='text-success'>↳ FCFE CAGR(3y) ≥ 20% : " + str(fcfe_cagr_prior3y) + '% per year!')
                elif fcfe_cagr_prior3y > 0 and fcfe_cagr_prior3y < 20:
                    w.append(Score.w_FCFE_growth_2000bp)
                    p.append(Score.w_FCFE_growth_2000bp * Score.pf_mod)
                    return Markup("<br>\t\t\t\t\t\t<span class='text-danger'>↳ FCFE CAGR(3y) < 20% : " + str(fcfe_cagr_prior3y) + '% per year!')
                elif fcfe_cagr_prior3y <= 0:
                    w.append(Score.w_FCFE_growth_2000bp)
                    p.append(Score.w_FCFE_growth_2000bp * Score.pf_neg)
                    return Markup("<br>\t\t\t\t\t\t<span class='text-danger'>↳ FCFE CAGR(3y) NEGATIVE: " + str(fcfe_cagr_prior3y) + '% per year!')
        except:
            w.append(Score.w_FCFE_growth_2000bp)
            p.append(Score.w_FCFE_growth_2000bp * Score.pf_mod)
            return Markup("<br>❓ <span class='text-info'>No data about Free Cash Flow to Equity (FCFE) CAGR!")

    def buyBacksHistory(self):
        """ Buy back own shares/CFO: Consistently buy back own shares >7y
			No p.append for increasing or decreasing stock buybacks, because buybacks depend on opportunities for better capital allocation.
			Better to notice the opportunistic behaviour of management. That is not to repurchase own stock for consistently same amount of money! """
        data = self.data
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            buy_backs_y0 = -self._cell(cfs_t, 'Repurchase Of Stock', 0)
            buy_backs_y1 = -self._cell(cfs_t, 'Repurchase Of Stock', 1)
            buy_backs_y2 = -self._cell(cfs_t, 'Repurchase Of Stock', 2)
            buy_backs_y3 = -self._cell(cfs_t, 'Repurchase Of Stock', 3)
            cfo_y0 = self._cell(cfs_t, 'Total Cash From Operating Activities', 0)
            cfo_y1 = self._cell(cfs_t, 'Total Cash From Operating Activities', 1)
            cfo_y2 = self._cell(cfs_t, 'Total Cash From Operating Activities', 2)
            cfo_y3 = self._cell(cfs_t, 'Total Cash From Operating Activities', 3)
            bb_to_cfo_y0 = round(strict_divide(buy_backs_y0, cfo_y0) * 100, 2)
            bb_to_cfo_y1 = round(strict_divide(buy_backs_y1, cfo_y1) * 100, 2)
            bb_to_cfo_y2 = round(strict_divide(buy_backs_y2, cfo_y2) * 100, 2)
            bb_to_cfo_y3 = round(strict_divide(buy_backs_y3, cfo_y3) * 100, 2)
            bb_to_cfo_mean = round(strict_divide(bb_to_cfo_y0 + bb_to_cfo_y1 + bb_to_cfo_y2 + bb_to_cfo_y3, 4), 2)
            bb_y0 = round(strict_divide(buy_backs_y0, 1000000), 2)
            bb_y1 = round(strict_divide(buy_backs_y1, 1000000), 2)
            bb_y2 = round(strict_divide(buy_backs_y2, 1000000), 2)
            bb_y3 = round(strict_divide(buy_backs_y3, 1000000), 2)
            self.fundamentals['buyBacksToCFOHistory'] = ([self.y3, self.y2, self.y1, self.y0], [bb_to_cfo_y3, bb_to_cfo_y2, bb_to_cfo_y1, bb_to_cfo_y0])
            self.fundamentals['buyBacksHistory'] = ([self.y3, self.y2, self.y1, self.y0], [bb_y3, bb_y2, bb_y1, bb_y0])
            if pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 0)) == True and pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 1)) == True and (pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 2)) == True) and (pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 3)) == True):
                w.append(Score.w_bb)
                p.append(Score.w_bb * Score.pf_neg)
                return Markup("⛔ <span class='text-danger'>The company does NOT repurchase own stock!")
            elif pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 0)) != True and pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 1)) != True and (pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 2)) != True) and (pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 3)) != True):
                if bb_y0 < bb_y1 and bb_y1 < bb_y2 and (bb_y2 < bb_y3):
                    w.append(Score.w_bb)
                    p.append(Score.w_bb * Score.pf_pos)
                    return Markup("✅ The company repurchase own stock every year!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_y3) + ', ' + str(bb_y2) + ', ' + str(bb_y1) + ', ' + str(bb_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: BB consistently decreasing!<br>\t\t\t\t\t\t<span class='text-danger'>↳ Management believes stock is overvalued?!<br>\t\t\t\t\t\t<span class='text-danger'>↳ Oppertunities for better capital allocation?!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB/CFO: " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_to_cfo_y3) + '%, ' + str(bb_to_cfo_y2) + '%, ' + str(bb_to_cfo_y1) + '%, ' + str(bb_to_cfo_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(bb_to_cfo_mean) + '%')
                elif bb_y0 < bb_y1:
                    w.append(Score.w_bb)
                    p.append(Score.w_bb * Score.pf_pos)
                    return Markup("✅ The company repurchase own stock every year!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_y3) + ', ' + str(bb_y2) + ', ' + str(bb_y1) + ', ' + str(bb_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t\t<span class='text-success'>↳ BB " + str(self.y1) + ' > ' + str(self.y0) + ": Opportunistic buybacks!<br>\t\t\t\t\t\t<span class='text-danger'>↳ Management believes stock is currently overvalued ?!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB/CFO: " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_to_cfo_y3) + '%, ' + str(bb_to_cfo_y2) + '%, ' + str(bb_to_cfo_y1) + '%, ' + str(bb_to_cfo_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(bb_to_cfo_mean) + '%')
                elif bb_y0 > bb_y1 and bb_y1 > bb_y2 and (bb_y2 > bb_y3):
                    w.append(Score.w_bb)
                    p.append(Score.w_bb * Score.pf_pos)
                    return Markup("✅ The company repurchase own stock every year!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_y3) + ', ' + str(bb_y2) + ', ' + str(bb_y1) + ', ' + str(bb_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: BB consistently increasing!<br>\t\t\t\t\t\t<span class='text-success'>↳ Management believes stock is undervalued?!<br>\t\t\t\t\t\t<span class='text-danger'>↳ Fewer or no oppertunities for better capital allocation?!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB/CFO: " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_to_cfo_y3) + '%, ' + str(bb_to_cfo_y2) + '%, ' + str(bb_to_cfo_y1) + '%, ' + str(bb_to_cfo_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(bb_to_cfo_mean) + '%')
                elif bb_y0 > bb_y1:
                    w.append(Score.w_bb)
                    p.append(Score.w_bb * Score.pf_pos)
                    return Markup("✅ The company repurchase own stock every year!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_y3) + ', ' + str(bb_y2) + ', ' + str(bb_y1) + ', ' + str(bb_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t\t<span class='text-success'>↳ BB " + str(self.y1) + ' < ' + str(self.y0) + ": Opportunistic buybacks!<br>\t\t\t\t\t\t<span class='text-success'>↳ Management believes stock is currently undervalued ?!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB/CFO: " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_to_cfo_y3) + '%, ' + str(bb_to_cfo_y2) + '%, ' + str(bb_to_cfo_y1) + '%, ' + str(bb_to_cfo_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(bb_to_cfo_mean) + '%')
                elif bb_y0 == bb_y1 and bb_y1 == bb_y2 and (bb_y2 == bb_y3):
                    w.append(Score.w_bb)
                    p.append(Score.w_bb * Score.pf_pos)
                    return Markup("✅ The company repurchase own stock every year!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_y3) + ', ' + str(bb_y2) + ', ' + str(bb_y1) + ', ' + str(bb_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: BB amount fixed!<br>\t\t\t\t\t\t<span class='text-danger'>↳ Management not opportunistic to Stock Buybacks!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB/CFO: " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_to_cfo_y3) + '%, ' + str(bb_to_cfo_y2) + '%, ' + str(bb_to_cfo_y1) + '%, ' + str(bb_to_cfo_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(bb_to_cfo_mean) + '%')
                elif bb_y0 == bb_y1:
                    w.append(Score.w_bb)
                    p.append(Score.w_bb * Score.pf_pos)
                    return Markup("✅ The company repurchase own stock every year!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_y3) + ', ' + str(bb_y2) + ', ' + str(bb_y1) + ', ' + str(bb_y0) + ' mln ' + data['currency'] + "<br>\t\t\t\t\t\t<span class='text-danger'>↳ NO Opportunistic buybacks!<br>\t\t\t\t\t\t<span class='text-danger'>↳ BB " + str(self.y1) + ' = ' + str(self.y0) + " => Management currently not opportunistic to BB!<br>\t\t\t\t\t\t<span class='text-success'>↳ BB/CFO: " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_to_cfo_y3) + '%, ' + str(bb_to_cfo_y2) + '%, ' + str(bb_to_cfo_y1) + '%, ' + str(bb_to_cfo_y0) + "%<br>\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(bb_to_cfo_mean) + '%')
            elif pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 0)) == True or pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 1)) == True or pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 2)) == True or (pd.isna(self._cell(cfs_t, 'Repurchase Of Stock', 3)) == True):
                w.append(Score.w_bb)
                p.append(Score.w_bb * Score.pf_mod)
                return Markup("⛔ The company does NOT repurchase own stock every year!<br>\t\t\t\t\t\t<span class='text-danger'>↳ BB " + str(self.y3) + '-' + str(self.y0) + ': ' + str(bb_y3) + ', ' + str(bb_y2) + ', ' + str(bb_y1) + ', ' + str(bb_y0) + ' mln ' + data['currency'])
        except:
            w.append(Score.w_bb)
            p.append(Score.w_bb * Score.pf_mod)
            return Markup("❓ <span class='text-info'>No data about Stock Buybacks!")

    def dividendsHistory(self):
        """ Dividends per shares and Div/CFO: Consistently increasing dividends >7y """
        data = self.data
        cfs_t = self.cfs_t
        w = self.weights_list
        p = self.points_list
        try:
            stock = self.stock
            div = stock.get_dividends()
            div = div.resample('YE').sum()
            div = div.reset_index()
            div['Year'] = div['Date'].dt.year
            divTail = div.tail()
            divTail = divTail.sort_values(by='Date', ascending=False)
            divYear_latest = list(divTail['Year'])[0]
            divYear_y0 = list(divTail['Year'])[1]
            divYear_y1 = list(divTail['Year'])[2]
            divYear_y2 = list(divTail['Year'])[3]
            divYear_y3 = list(divTail['Year'])[4]
            divTail_latest = round(list(divTail['Dividends'])[0], 3)
            divTail_y0 = round(list(divTail['Dividends'])[1], 3)
            divTail_y1 = round(list(divTail['Dividends'])[2], 3)
            divTail_y2 = round(list(divTail['Dividends'])[3], 3)
            divTail_y3 = round(list(divTail['Dividends'])[4], 3)
            if str(divYear_latest) == str(self.ttm) or str(divYear_latest) == str(self.y0):
                div_cfs_y0 = -self._cell(cfs_t, 'Dividends Paid', 0)
                div_cfs_y1 = -self._cell(cfs_t, 'Dividends Paid', 1)
                div_cfs_y2 = -self._cell(cfs_t, 'Dividends Paid', 2)
                div_cfs_y3 = -self._cell(cfs_t, 'Dividends Paid', 3)
                cfo_y0 = self._cell(cfs_t, 'Total Cash From Operating Activities', 0)
                cfo_y1 = self._cell(cfs_t, 'Total Cash From Operating Activities', 1)
                cfo_y2 = self._cell(cfs_t, 'Total Cash From Operating Activities', 2)
                cfo_y3 = self._cell(cfs_t, 'Total Cash From Operating Activities', 3)
                div_to_cfo_y0 = round(strict_divide(div_cfs_y0, cfo_y0) * 100, 2)
                div_to_cfo_y1 = round(strict_divide(div_cfs_y1, cfo_y1) * 100, 2)
                div_to_cfo_y2 = round(strict_divide(div_cfs_y2, cfo_y2) * 100, 2)
                div_to_cfo_y3 = round(strict_divide(div_cfs_y3, cfo_y3) * 100, 2)
                div_to_cfo_mean = round(strict_divide(div_to_cfo_y0 + div_to_cfo_y1 + div_to_cfo_y2 + div_to_cfo_y3, 4), 2)
                self.fundamentals['dividendsToCFOHistory'] = ([self.y3, self.y2, self.y1, self.y0], [div_to_cfo_y3, div_to_cfo_y2, div_to_cfo_y1, div_to_cfo_y0])
                self.fundamentals['dividendsHistory'] = ([self.y3, self.y2, self.y1, self.y0], [strict_divide(div_cfs_y3, 1000000), strict_divide(div_cfs_y2, 1000000), strict_divide(div_cfs_y1, 1000000), strict_divide(div_cfs_y0, 1000000)])
                if (divTail_latest == 0 or divTail_y0 == 0 or divTail_y1 == 0 or (divTail_y2 == 0) or (divTail_y3 == 0)) and (divTail_latest != 0 or divTail_y0 != 0 or divTail_y1 != 0 or (divTail_y2 != 0) or (divTail_y3 != 0)):
                    w.append(Score.w_dividends)
                    p.append(Score.w_dividends * Score.pf_mod)
                    return Markup("⛔ The company doesn't pay dividends every year!<br>\t\t\t\t\t\t<span class='text-danger'>↳ " + str(divYear_y3) + '-' + str(divYear_latest) + ': ' + str(divTail_y3) + ', ' + str(divTail_y2) + ', ' + str(divTail_y1) + ', ' + str(divTail_y0) + ', ' + str(divTail_latest) + ' ' + data['currency'])
                elif divTail_latest != 0 and divTail_y0 != 0 and (divTail_y1 != 0) and (divTail_y2 != 0) and (divTail_y3 != 0):
                    if divTail_y0 == divTail_y1 and divTail_y1 == divTail_y2 and (divTail_y2 == divTail_y3):
                        w.append(Score.w_dividends)
                        p.append(Score.w_dividends * Score.pf_pos)
                        w.append(Score.w_dividends_increasing)
                        p.append(Score.w_dividends_increasing * Score.pf_mod)
                        return Markup("✅ The company pays dividends every year!<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(divYear_y3) + '-' + str(divYear_latest) + ': ' + str(divTail_y3) + ', ' + str(divTail_y2) + ', ' + str(divTail_y1) + ', ' + str(divTail_y0) + ', ' + str(divTail_latest) + ' ' + data['currency'] + "<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ Fixed yearly dividend per share!<br>\t\t\t\t\t\t\t<span class='text-success'>↳ Div/CFO: " + str(divYear_y3) + '-' + str(divYear_y0) + ': ' + str(div_to_cfo_y3) + '%, ' + str(div_to_cfo_y2) + '%, ' + str(div_to_cfo_y1) + '%, ' + str(div_to_cfo_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(div_to_cfo_mean) + '%')
                    if (divTail_y0 < divTail_y1 or divTail_y1 < divTail_y2 or divTail_y2 < divTail_y3) and (divTail_y0 < divTail_y1 and divTail_y1 < divTail_y2 and (divTail_y2 < divTail_y3)):
                        w.append(Score.w_dividends)
                        p.append(Score.w_dividends * Score.pf_pos)
                        w.append(Score.w_dividends_decreasing)
                        p.append(Score.w_dividends_decreasing * Score.pf_neg)
                        return Markup("✅ The company pays dividends every year!<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(divYear_y3) + '-' + str(divYear_latest) + ': ' + str(divTail_y3) + ', ' + str(divTail_y2) + ', ' + str(divTail_y1) + ', ' + str(divTail_y0) + ', ' + str(divTail_latest) + ' ' + data['currency'] + "<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ CAVE: Yearly dividend per share consistently decreasing!<br>\t\t\t\t\t\t\t<span class='text-success'>↳ Div/CFO: " + str(divYear_y3) + '-' + str(divYear_y0) + ': ' + str(div_to_cfo_y3) + '%, ' + str(div_to_cfo_y2) + '%, ' + str(div_to_cfo_y1) + '%, ' + str(div_to_cfo_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(div_to_cfo_mean) + '%')
                    if (divTail_y0 < divTail_y1 or divTail_y1 < divTail_y2 or divTail_y2 < divTail_y3) and divTail_y0 > divTail_y3:
                        w.append(Score.w_dividends)
                        p.append(Score.w_dividends * Score.pf_pos)
                        w.append(Score.w_dividends_increasing)
                        p.append(Score.w_dividends_increasing * Score.pf_mod)
                        return Markup("✅ The company pays dividends every year!<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(divYear_y3) + '-' + str(divYear_latest) + ': ' + str(divTail_y3) + ', ' + str(divTail_y2) + ', ' + str(divTail_y1) + ', ' + str(divTail_y0) + ', ' + str(divTail_latest) + ' ' + data['currency'] + "<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ Yearly dividend per share not consistently increasing!<br>\t\t\t\t\t\t\t<span class='text-success'>↳ although: Div per share " + str(divYear_y3) + ' < ' + str(divYear_y0) + ' (' + str(divTail_y3) + ' < ' + str(divTail_y0) + ' ' + data['currency'] + " per share)<br>\t\t\t\t\t\t\t<span class='text-success'>↳ Div/CFO: " + str(divYear_y3) + '-' + str(divYear_y0) + ': ' + str(div_to_cfo_y3) + '%, ' + str(div_to_cfo_y2) + '%, ' + str(div_to_cfo_y1) + '%, ' + str(div_to_cfo_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(div_to_cfo_mean) + '%')
                    if divTail_y0 < divTail_y1 or divTail_y1 < divTail_y2 or divTail_y2 < divTail_y3:
                        w.append(Score.w_dividends)
                        p.append(Score.w_dividends * Score.pf_pos)
                        w.append(Score.w_dividends_increasing)
                        p.append(Score.w_dividends_increasing * Score.pf_neg)
                        return Markup("✅ The company pays dividends every year!<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(divYear_y3) + '-' + str(divYear_latest) + ': ' + str(divTail_y3) + ', ' + str(divTail_y2) + ', ' + str(divTail_y1) + ', ' + str(divTail_y0) + ', ' + str(divTail_latest) + ' ' + data['currency'] + "<br>\t\t\t\t\t\t\t<span class='text-danger'>↳ Yearly dividend per share not consistently increasing!<br>\t\t\t\t\t\t\t<span class='text-success'>↳ Div/CFO: " + str(divYear_y3) + '-' + str(divYear_y0) + ': ' + str(div_to_cfo_y3) + '%, ' + str(div_to_cfo_y2) + '%, ' + str(div_to_cfo_y1) + '%, ' + str(div_to_cfo_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(div_to_cfo_mean) + '%')
                    if divTail_y0 > divTail_y1 and divTail_y1 > divTail_y2 and (divTail_y2 > divTail_y3):
                        w.append(Score.w_dividends)
                        p.append(Score.w_dividends * Score.pf_pos)
                        w.append(Score.w_dividends_increasing)
                        p.append(Score.w_dividends_increasing * Score.pf_pos)
                        return Markup("✅ The company pays dividends every year!<br>\t\t\t\t\t\t\t<span class='text-success'>↳ " + str(divYear_y3) + '-' + str(divYear_latest) + ': ' + str(divTail_y3) + ', ' + str(divTail_y2) + ', ' + str(divTail_y1) + ', ' + str(divTail_y0) + ', ' + str(divTail_latest) + ' ' + data['currency'] + "<br>\t\t\t\t\t\t\t<span class='text-success'>↳ Yearly dividend per share consistently increasing!<br>\t\t\t\t\t\t\t<span class='text-success'>↳ Div/CFO: " + str(divYear_y3) + '-' + str(divYear_y0) + ': ' + str(div_to_cfo_y3) + '%, ' + str(div_to_cfo_y2) + '%, ' + str(div_to_cfo_y1) + '%, ' + str(div_to_cfo_y0) + "%<br>\t\t\t\t\t\t\t<span class='text-success'>↳ mean: " + str(div_to_cfo_mean) + '%')
            else:
                divTimeLapse = self.ttm - divYear_latest
                w.append(Score.w_dividends)
                p.append(Score.w_dividends * Score.pf_neg)
                return Markup('⛔ The company does NOT pay dividends ANYMORE !<br>↳ Last payment: ' + str(divYear_latest) + '<br>↳ ' + str(divYear_y3) + '-' + str(divYear_latest) + ': ' + str(divTail_y3) + ', ' + str(divTail_y2) + ', ' + str(divTail_y1) + ', ' + str(divTail_y0) + ', ' + str(divTail_latest) + ' ' + data['currency'] + "/share<br>\t\t\t\t\t<span class='text-danger'>↳ It's been " + str(divTimeLapse) + ' years since the company last paid a dividend!')
        except:
            w.append(Score.w_dividends)
            p.append(Score.w_dividends * Score.pf_neg)
            return Markup("⛔ <span class='text-danger'>The company does NOT pay dividends!")

    def incomeStatement(self):
        """ Income Statement (Profit & Loss Statement)  """
        data = self.data
        pal = self.pal
        try:
            pal_mln = round(strict_divide(pal, 1000000), 2)
            ' Reindexing or changing the order of rows Income Statement '
            order_pal = ['Total Revenue', 'Cost Of Revenue', 'Gross Profit', 'Selling General Administrative', 'Research Development', 'Other Operating Expenses', 'Total Operating Expenses', 'Operating Income', 'Items', 'Other Items', 'Ebit', 'Interest Expense', 'Total Other Income Expense Net', 'Income Before Tax', 'Income Tax Expense', 'Minority Interest', 'Net Income From Continuing Ops', 'Discontinued Operations', 'Non Recurring', 'Extraordinary', 'Effect Of Accounting Charges', 'Net Income', 'Net Income Applicable To Common Shares']
            pal_mln_ordered = pal_mln.reindex(order_pal)
            return Markup('Income Statement '.upper() + '(in million ' + data['currency'] + ')<br>' + str(pd.DataFrame(pal_mln_ordered).to_html()))
        except:
            return Markup("❓ <span class='text-info'>No data about Income Statement (P&L)!")

    def cashflowStatement(self):
        """ Cashflow Statement  """
        data = self.data
        cfs = self.cfs
        try:
            cfs_mln = round(strict_divide(cfs, 1000000), 2)
            ' Reindexing or changing the order of rows Cashflow Statement '
            order_cfs = ['Net Income', 'Depreciation', 'Change To Netincome', 'Change To Account Receivables', 'Change To Inventory', 'Change To Operating Activities', 'Change To Liabilities', 'Total Cash From Operating Activities', 'Capital Expenditures', 'Investments', 'Other Cashflows From Investing Activities', 'Total Cashflows From Investing Activities', 'Net Borrowings', 'Issuance Of Stock', 'Repurchase Of Stock', 'Dividends Paid', 'Other Cashflows From Financing Activities', 'Total Cash From Financing Activities', 'Change In Cash']
            cfs_mln_ordered = cfs_mln.reindex(order_cfs)
            return Markup('Cashflow Statement '.upper() + '(in million ' + data['currency'] + ')<br>' + str(pd.DataFrame(cfs_mln_ordered).to_html()))
        except:
            return Markup("❓ <span class='text-info'>No data about Cashflow Statement!")

    def cashflowStatementChangesInCash(self):
        """ Cashflow Statement: Changes in Cash  """
        data = self.data
        cfs = self.cfs
        try:
            cfs_mln = round(strict_divide(cfs, 1000000), 2)
            ' Reindexing or changing the order of rows Cashflow Statement '
            order_cfs_changesincash = ['Total Cash From Operating Activities', 'Total Cashflows From Investing Activities', 'Total Cash From Financing Activities', 'Change In Cash']
            cfs_mln_ordered_changesincash = cfs_mln.reindex(order_cfs_changesincash)
            return Markup('Changes in Cash (in million ' + data['currency'] + ')<br>' + str(pd.DataFrame(cfs_mln_ordered_changesincash).to_html()))
        except:
            return Markup("❓ <span class='text-info'>No data about Cashflow Statement: Changes in Cash!")

    def balanceSheet(self):
        """ Balance Sheet """
        data = self.data
        bs = self.bs
        try:
            bs_mln = round(strict_divide(bs, 1000000), 2)
            ' Reindexing or changing the order of rows Balance Sheet '
            order_bs = ['Cash', 'Short Term Investments', 'Net Receivables', 'Inventory', 'Other Current Assets', 'Total Current Assets', 'Intangible Assets', 'Good Will', 'Property Plant Equipment', 'Long Term Investments', 'Deferred Long Term Asset Charges', 'Other Assets', 'Total Assets', 'Accounts Payable', 'Short Long Term Debt', 'Other Current Liab', 'Total Current Liabilities', 'Long Term Debt', 'Other Liab', 'Total Liab', 'Common Stock', 'Retained Earnings', 'Capital Surplus', 'Treasury Stock', 'Other Stockholder Equity', 'Total Stockholder Equity', 'Minority Interest', 'Net Tangible Assets']
            bs_mln_ordered = bs_mln.reindex(order_bs)
            return Markup('Balance Sheet '.upper() + '(in million ' + data['currency'] + ')<br>' + str(pd.DataFrame(bs_mln_ordered).to_html()))
        except:
            return Markup("❓ <span class='text-info'>No data about Balance Sheet!")

    def score(self):
        """ Total score """
        w = self.weights_list
        p = self.points_list
        try:
            weights_total = round(sum(w), 2)
            points_total = round(sum(p), 2)
            if weights_total > 0:
                points_percentage = round(strict_divide(points_total, weights_total) * 100, 2)
                self.fundamentals['score'] = [points_total, weights_total, points_percentage]
                if points_percentage < 45:
                    return Markup('<strong><u>TTW SCORE & CONCLUSION</u></strong><br><br>\t\t\t\t\t\t❌❌❌<br><br><u>TTW Score: '.upper() + "</u><br>\t\t\t\t\t\t<span class='fs-2 text-danger'><strong>" + str(points_percentage) + "%</strong></span><br><br>\t\t\t\t\t\tTHIS STOCK IS 🙉🙈🙊 !<br>\t\t\t\t\t\tDON'T EVEN THINK ABOUT INVESTING IN THIS ONE!<br><br>\t\t\t\t\t\t<strong>CONCLUSION:</strong><br>")
                if points_percentage >= 45 and points_percentage < 55:
                    return Markup('<strong><u>TTW SCORE & CONCLUSION</u></strong><br><br>\t\t\t\t\t\t⭐<br><br><u>TTW Score: '.upper() + "</u><br>\t\t\t\t\t\t<span class='fs-2 text-dark'><strong>" + str(points_percentage) + "%</strong></span><br><br>\t\t\t\t\t\tThis stock is <u>MODERATE!</u><br>DON'T INVEST IN THIS ONE!<br><br>\t\t\t\t\t\t<strong>CONCLUSION:</strong><br>")
                if points_percentage >= 55 and points_percentage < 65:
                    return Markup('<strong><u>TTW SCORE & CONCLUSION</u></strong><br><br>\t\t\t\t\t\t⭐⭐<br><br><u>TTW Score: '.upper() + "</u><br>\t\t\t\t\t\t<span class='fs-2 text-secondary'><strong>" + str(points_percentage) + '%</strong></span><br><br>\t\t\t\t\t\tThis stock is <u>BETWEEN MODERATE AND GOOD!</u><br>\t\t\t\t\t\tYOU SHOULD NOT CONSIDER TO INVEST IN THIS ONE!<br><br>\t\t\t\t\t\t<strong>CONCLUSION:</strong><br>')
                if points_percentage >= 65 and points_percentage < 75:
                    return Markup('<strong><u>TTW SCORE & CONCLUSION</u></strong><br><br>\t\t\t\t\t\t⭐⭐⭐<br><br><u>TTW Score: '.upper() + "</u><br>\t\t\t\t\t\t<span class='fs-2 text-info'><strong>" + str(points_percentage) + '%</strong></span><br><br>\t\t\t\t\t\tThis stock is <u>VERY GOOD!</u><br>\t\t\t\t\t\tYOU MAY CONSIDER TO INVEST IN THIS ONE!<br><br>\t\t\t\t\t\t<strong>CONCLUSION:</strong><br>')
                if points_percentage >= 75 and points_percentage < 85:
                    return Markup('<strong><u>TTW SCORE & CONCLUSION</u></strong><br><br>\t\t\t\t\t\t⭐⭐⭐⭐<br><br><u>TTW Score: '.upper() + "</u><br>\t\t\t\t\t\t<span class='fs-2 text-primary'><strong>" + str(points_percentage) + '%</strong></span><br><br>\t\t\t\t\t\tThis stock is <u>EXCELLENT!</u><br>YOU SHOULD CONSIDER TO INVEST IN THIS ONE!<br><br>\t\t\t\t\t\t<strong>CONCLUSION:</strong><br>')
                if points_percentage >= 85 and points_percentage <= 100:
                    return Markup('<strong><u>TTW SCORE & CONCLUSION</u></strong><br><br>\t\t\t\t\t\t⭐⭐⭐⭐⭐<br><br><u>TTW Score: '.upper() + "</u><br>\t\t\t\t\t\t<span class='fs-2 text-success'><strong>" + str(points_percentage) + '%</strong></span><br><br>\t\t\t\t\t\t✨✨✨ 💰 JACKPOT 💰 ✨✨✨<br><br>\t\t\t\t\t\tThis stock is <u>WONDERFUL!!!!!</u><br>YOU ARE A FOOL IF YOU HESITATE TO INVEST IN THIS ONE!<br><br>\t\t\t\t\t\t<strong>CONCLUSION:</strong><br>')
            if weights_total <= 0:
                return Markup('<br>⚠ Not possible to calculate TTW Score: denominator = ZERO !')
        except:
            return Markup("❓ <span class='text-info'>No data about TTW Score!")

    def rank(self):
        """ Ranking the total score """
        weights_list = self.weights_list
        points_list = self.points_list
        weights_tot = sum(weights_list)
        points_tot = sum(points_list)
        ranking = strict_divide(points_tot, weights_tot)
        return ranking

    def intrinsicValue(self):
        """ Intrinsic value valuation """
        data = self.data
        cfs_t = self.cfs_t
        ' P/FCF Multiple '
        multiple_PFCF = self.multiple_PFCF
        ' Discount Rate '
        discount_rate = self.discount_rate
        if discount_rate > 1:
            discount_rate = strict_divide(discount_rate, 100)
        ' FCF Growth rates (CAGR): Conservative approach if not defined '
        if self.growthRate_p5y != None:
            g_fcf = self.growthRate_p5y
        else:
            g_fcf = 0
        if self.growthRate_n5y != None:
            growthRate_n5y = self.growthRate_n5y
        else:
            growthRate_n5y = 0
        try:
            if data['revenueGrowth'] != None:
                growthRevenue = data['revenueGrowth']
            else:
                growthRevenue = 0
        except:
            growthRevenue = 0
        growth_FCF = self.growth_FCF
        if growth_FCF == None:
            if growthRate_n5y < g_fcf:
                g_fcf = growthRate_n5y
            if g_fcf <= 0:
                if growthRevenue <= 0.15 and growthRevenue > 0:
                    g_fcf = growthRevenue
                elif growthRevenue > 0.15:
                    g_fcf = 0.15
                else:
                    g_fcf = 0
        else:
            if growth_FCF > 1:
                growth_FCF = strict_divide(growth_FCF, 100)
            g_fcf = growth_FCF
        ' FCFE Calculation '
        FCFE = self.FCFE
        if FCFE == None:
            try:
                cfo_y0 = self._cell(cfs_t, 'Total Cash From Operating Activities', 0)
                capex_y0 = -self._cell(cfs_t, 'Capital Expenditures', 0)
                net_borrowings_y0 = self._cell(cfs_t, 'Net Borrowings', 0)
                fcfe = cfo_y0 - capex_y0 + net_borrowings_y0
                if pd.isna(fcfe) == True or (fcfe < 0 and data['freeCashflow'] != None):
                    fcfe = data['freeCashflow']
            except (KeyError, TypeError):
                return Markup("❓ <span class='text-info'>No data about FCFE. Intrinsic Value not calculated!")
        else:
            fcfe = FCFE * 1000000
        ' Intrinsic value valuation '
        if fcfe > 0:
            ' Calculation FCFE after 1 to 10 year '
            fcfe_1y = fcfe * (1 + g_fcf) ** 1
            fcfe_2y = fcfe * (1 + g_fcf) ** 2
            fcfe_3y = fcfe * (1 + g_fcf) ** 3
            fcfe_4y = fcfe * (1 + g_fcf) ** 4
            fcfe_5y = fcfe * (1 + g_fcf) ** 5
            fcfe_6y = fcfe * (1 + g_fcf) ** 6
            fcfe_7y = fcfe * (1 + g_fcf) ** 7
            fcfe_8y = fcfe * (1 + g_fcf) ** 8
            fcfe_9y = fcfe * (1 + g_fcf) ** 9
            fcfe_10y = fcfe * (1 + g_fcf) ** 10
            ' Calculation Terminal Value after 10 year '
            tv_10y = fcfe_10y * multiple_PFCF
            ' Discounting to present value => Default discount rate = 0.12 (NB: adjusted for current month) '
            adjustForCurrentMonth = strict_divide(1, 12) * datetime.now().month
            dfcfe_1y = strict_divide(fcfe_1y, (1 + discount_rate) ** (1 - adjustForCurrentMonth))
            dfcfe_2y = strict_divide(fcfe_2y, (1 + discount_rate) ** (2 - adjustForCurrentMonth))
            dfcfe_3y = strict_divide(fcfe_3y, (1 + discount_rate) ** (3 - adjustForCurrentMonth))
            dfcfe_4y = strict_divide(fcfe_4y, (1 + discount_rate) ** (4 - adjustForCurrentMonth))
            dfcfe_5y = strict_divide(fcfe_5y, (1 + discount_rate) ** (5 - adjustForCurrentMonth))
            dfcfe_6y = strict_divide(fcfe_6y, (1 + discount_rate) ** (6 - adjustForCurrentMonth))
            dfcfe_7y = strict_divide(fcfe_7y, (1 + discount_rate) ** (7 - adjustForCurrentMonth))
            dfcfe_8y = strict_divide(fcfe_8y, (1 + discount_rate) ** (8 - adjustForCurrentMonth))
            dfcfe_9y = strict_divide(fcfe_9y, (1 + discount_rate) ** (9 - adjustForCurrentMonth))
            dfcfe_10y = strict_divide(fcfe_10y, (1 + discount_rate) ** (10 - adjustForCurrentMonth))
            dtv_10y = strict_divide(tv_10y, (1 + discount_rate) ** (10 - adjustForCurrentMonth))
            ivps_dcf = dfcfe_1y + dfcfe_2y + dfcfe_3y + dfcfe_4y + dfcfe_5y + dfcfe_6y + dfcfe_7y + dfcfe_8y + dfcfe_9y + dfcfe_10y + dtv_10y
            try:
                ivps_dcf_ps = strict_divide(ivps_dcf, data['sharesOutstanding'])
            except:
                return Markup("❓ <span class='text-info'>No data about Shares Outstanding. Intrinsic Value not calculated!")
            margin_of_safety = -((strict_divide(data['currentPrice'], ivps_dcf_ps) - 1) * 100)
            self.fundamentals['intrinsicValue'] = [fcfe, margin_of_safety]
        ' Result Intrinsic Value '
        try:
            if fcfe > 0:
                if ivps_dcf_ps * 1.1 < data['currentPrice']:
                    return Markup('<strong><u>VALUATION</u></strong><br><br>\t\t\t\t\t\tCurrent stock price: ' + str('{:,}'.format(round(data['currentPrice'], 2))) + ' ' + data['currency'] + '<br>\t\t\t\t\t\t52w change: ' + str(round(data['52WeekChange'] * 100, 2)) + '%' + '<br>\t\t\t\t\t\tShares outstanding: ' + str('{:,}'.format(round(strict_divide(data['sharesOutstanding'], 1000000), 3))) + " mln<br><br>\t\t\t\t\t\t<u>Intrinsic value per share:</u><br><strong><span class='fs-2 text-danger'>" + str('{:,}'.format(round(ivps_dcf_ps, 1))) + ' ' + data['currency'] + '</strong><br>\t\t\t\t\t\tFCFE:' + str(round(strict_divide(fcfe, 1000000000), 1)) + ' bln ' + data['currency'] + '<br>\t\t\t\t\t\tP/CF multiple: ' + str(multiple_PFCF) + ', DR: ' + str(round(discount_rate * 100, 1)) + '%, g: ' + str(round(g_fcf * 100, 1)) + "%<br>\t\t\t\t\t\t<span class='fs-2 text-danger'><strong>OVERVALUED</strong></span>")
                elif ivps_dcf_ps * 0.9 > data['currentPrice']:
                    gain_potential = (strict_divide(ivps_dcf_ps, data['currentPrice']) - 1) * 100
                    return Markup('<strong><u>VALUATION</u></strong><br><br>\t\t\t\t\t\tCurrent stock price: ' + str('{:,}'.format(round(data['currentPrice'], 2))) + ' ' + data['currency'] + '<br>\t\t\t\t\t\t52w change: ' + str(round(data['52WeekChange'] * 100, 2)) + '%' + '<br>\t\t\t\t\t\tShares outstanding: ' + str('{:,}'.format(round(strict_divide(data['sharesOutstanding'], 1000000), 3))) + " mln<br><br>\t\t\t\t\t\t<u>Intrinsic value per share:</u><br><strong><span class='fs-2 text-success'>" + str('{:,}'.format(round(ivps_dcf_ps, 1))) + ' ' + data['currency'] + '</strong><br>\t\t\t\t\t\tFCFE:' + str(round(strict_divide(fcfe, 1000000000), 1)) + ' bln ' + data['currency'] + '<br>\t\t\t\t\t\tP/CF multiple: ' + str(multiple_PFCF) + ', DR: ' + str(round(discount_rate * 100, 1)) + '%, g: ' + str(round(g_fcf * 100, 1)) + "%<br>\t\t\t\t\t\t<span class='fs-2 text-success'><strong>UNDERVALUED</strong></span><span class='text-success'><br>\t\t\t\t\t\t↳ Margin of Safety: " + str(round(margin_of_safety, 1)) + '%<br>\t\t\t\t\t\t↳ Potential gain: ' + str(round(gain_potential, 1)) + '%')
                elif ivps_dcf_ps * 1.1 >= data['currentPrice'] and ivps_dcf_ps * 0.9 <= data['currentPrice']:
                    return Markup('<strong><u>VALUATION</u></strong><br><br>\t\t\t\t\t\tCurrent stock price: ' + str('{:,}'.format(round(data['currentPrice'], 2))) + ' ' + data['currency'] + '<br>\t\t\t\t\t\t52w change: ' + str(round(data['52WeekChange'] * 100, 2)) + '%' + '<br>\t\t\t\t\t\tShares outstanding: ' + str('{:,}'.format(round(strict_divide(data['sharesOutstanding'], 1000000), 3))) + " mln<br><br>\t\t\t\t\t\t<u>Intrinsic value per share:</u><br><strong><span class='fs-2 text-info'>" + str('{:,}'.format(round(ivps_dcf_ps, 1))) + ' ' + data['currency'] + '</strong><br>\t\t\t\t\t\tFCFE:' + str(round(strict_divide(fcfe, 1000000000), 1)) + ' bln ' + data['currency'] + '<br>\t\t\t\t\t\tP/CF multiple: ' + str(multiple_PFCF) + ', DR: ' + str(round(discount_rate * 100, 1)) + '%, g: ' + str(round(g_fcf * 100, 1)) + "%<br>\t\t\t\t\t\t<span class='fs-2 text-info'><strong>FAIRLY PRICED</strong></span>")
            elif fcfe == 0:
                return Markup('<strong><u>VALUATION</u></strong><br><br>\t\t\t\t\tCurrent stock price: ' + str('{:,}'.format(round(data['currentPrice'], 2))) + ' ' + data['currency'] + '<br>\t\t\t\t\t52w change: ' + str(round(data['52WeekChange'] * 100, 2)) + '%' + '<br>\t\t\t\t\tShares outstanding: ' + str('{:,}'.format(round(strict_divide(data['sharesOutstanding'], 1000000), 3))) + ' mln<br><br>\t\t\t\t\tFCFE is ZERO!<br>\t\t\t\t\tCalculation Intrinsic Value <strong>NOT POSSIBLE</strong> with DCF-method!')
            else:
                return Markup('<strong><u>VALUATION</u></strong><br><br>\t\t\t\t\tCurrent stock price: ' + str('{:,}'.format(round(data['currentPrice'], 2))) + ' ' + data['currency'] + '<br>\t\t\t\t\t52w change: ' + str(round(data['52WeekChange'] * 100, 2)) + '%' + '<br>\t\t\t\t\tShares outstanding: ' + str('{:,}'.format(round(strict_divide(data['sharesOutstanding'], 1000000), 3))) + ' mln<br><br>\t\t\t\t\tFCFE is NEGATIVE!<br>\t\t\t\t\tCalculation Intrinsic Value <strong>NOT POSSIBLE</strong> with DCF-method!')
        except:
            return Markup("❓ <span class='text-info'>No data about intrinsic value!")

    def conclusion(self):
        """ Conclusion """
        try:
            score = list(self.fundamentals['score'])[2]
            margin_of_safety = list(self.fundamentals['intrinsicValue'])[1]
            roe = list(self.fundamentals['returnOnEquityHistory'])[1][4]
            ronta = list(self.fundamentals['returnOnNetTangibleAssetsHistory'])[1][3]
            roa = list(self.fundamentals['returnOnAssetsHistory'])[1][4]
            dte = list(self.fundamentals['debtToEquityHistory'])[1][4]
            cr = list(self.fundamentals['currentRatioHistory'])[1][3]
            if score >= 75 and margin_of_safety > 25 and (roe > 15) and (ronta > 15) and (roa > 1) and (dte < 50) and (cr > 1):
                return Markup('🟢 GREEN LIGHT for a BUY !!!')
            elif score >= 75 and margin_of_safety < 25 and (roe > 15) and (ronta > 15) and (roa > 1) and (dte < 50) and (cr > 1):
                return Markup('🟡 YELLOW LIGHT: WAIT for a better price!')
            else:
                return Markup('🔴 RED LIGHT: Keep searching for a better opportunity!')
        except:
            return Markup('🔴 RED LIGHT: Keep searching for a better opportunity!')
