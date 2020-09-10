
import datetime
import requests, lxml
from bs4 import BeautifulSoup
import pandas as pd

user_date = input("Please enter a valid date (format YYYYMMDD): ")

headers = {
    'user-agent':
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0'
}
url_currency = "https://www3.bcb.gov.br/bc_moeda/rest/moeda/data"
url_search = "https://www3.bcb.gov.br/bc_moeda/rest/converter/1/1/"
url_exchange_date = "https://www3.bcb.gov.br/bc_moeda/rest/cotacao/fechamento/ultima/1/220/"


def main():
    list_curr = []
    date_search = format_date(user_date)

    if date_search.__len__() == 10:
        with requests.Session() as s:
            req = s.get(url_exchange_date + str(date_search), headers=headers, verify=True)
            soup = BeautifulSoup(req.content, 'lxml-xml')
            date_exchange = soup.find("dataHoraCotacao").get_text()[:10]
            if date_exchange == date_search:
                req = s.get(url_currency, headers=headers, verify=True)
                soup = BeautifulSoup(req.content, 'lxml-xml')
                for curr in soup.find_all("moeda"):
                    dic_curr = {}
                    dic_curr['id'] = curr.codigo.get_text()
                    dic_curr['currency'] = curr.simbolo.get_text()
                    dic_curr['land'] = curr.nomeFormatado.get_text()
                    dic_curr['value'] = 0
                    list_curr.append(dic_curr)

                df = pd.DataFrame(list_curr)
                df = get_exchange_rate(df, date_search)
                print(f"{df['currency']},{df['land']},{format_value(df['value'])}")
            else:
                print("X")
    else:
        print("Error: Date does not match format YYYYMMDD or is not valid.")


def format_url(dolarid, currencyid, date):
    """
        :param dolarid: dolar id
        :param currencyid: currency id to convert
        :param date: date of the exchage
        :return: format url to use in Banco Central's API
    """
    return f"https://www3.bcb.gov.br/bc_moeda/rest/converter/1/1/{currencyid}/{dolarid}/{date}"


def format_date(_date):
    """
        :param _date: date in YYYYMMDD format
        :return:  date to YYYY-MM-DD  format
    """
    try:
        if _date and not isinstance(_date, datetime.date):
            _date = datetime.datetime.strptime(_date, '%Y%m%d').date()
        if _date:
             _date = '%04d-%02d-%02d' % (_date.year, _date.month, _date.day)
        else:
            _date = ''
    except Exception as e:
        _date = ''
    return _date


def format_value(dolar_value):
    """
        :param dolar_value: original value
        :return: format value
    """
    return '{0:.10f}'.format(dolar_value).rstrip("0")


def get_exchange_rate(df, date_search):
    """
        :param df: dataframe wih currencies
        :param date_search: date of exchange rate
        :return: dataframe with the lowest exchange rate against dolar according to Banco Central website
    """
    dolarid = df.loc[df['currency'] == 'USD'].id.item()
    print("Getting exchange rates data, please wait... ")
    with requests.Session() as s:
        for i, row in df.iterrows():
            url_temp = format_url(dolarid, row['id'], date_search)
            req = s.get(url_temp, headers=headers, verify=True)
            if req.status_code != 404:
                soup = BeautifulSoup(req.content, 'lxml-xml')
                dolarvalue = soup.find("valor-convertido")
                df.iloc[i, df.columns.get_loc('value')] = float(dolarvalue.get_text())
    df= df[df['value'] != 0]
    return df.loc[df['value'].idxmin()]


if __name__ == "__main__":
    main()
