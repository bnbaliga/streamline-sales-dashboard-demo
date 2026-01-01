import yfinance as yf

microsoft = yf.Ticker('MSFT')
microsoft.income_stmt
microsoft.balance_sheet
microsoft.cash_flow

print(microsoft.income_stmt)
