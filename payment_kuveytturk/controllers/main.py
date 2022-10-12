import base64
import hashlib
from logging import getLogger

import werkzeug

from odoo import http
from odoo.http import request
import requests
from urllib.parse import unquote
from ..tools import config

_logger = getLogger(__name__)


class PaymentKuveytTurkController(http.Controller):
    _kuveytturk_callback_url = '/payment/kuveytturk/callback'
    _kuveytturk_callback_url_ok = f'{_kuveytturk_callback_url}/ok-url'
    _kuveytturk_callback_url_fail = f'{_kuveytturk_callback_url}/fail-url'

    @property
    def kuveytturk_callback_url(self):
        return self._kuveytturk_callback_url

    def __get_provider(self):
        return request.env["payment.acquirer"].sudo().search([('provider', '=', 'kuveytturk')])

    _kuveytturk_payment_url = "/shop/payment/pay"

    @http.route([_kuveytturk_payment_url], type='http',
                methods=["GET", "POST"], auth="public", website=False, csrf=False, cors="none")
    def kuveytturk_payment(self, **kwargs):
        provider_obj = self.__get_provider()
        if provider_obj.state == "enabled":
            kart_onay_url = config.SANAL_POS["live_kart_onay_url"]
        else:
            kart_onay_url = config.SANAL_POS["test_kart_onay_url"]
        kwargs.update(request.httprequest.data)
        string_data = '<KuveytTurkVPosMessage xmlns:xsi="http://www.w3.org/2001/XMLSchemainstance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">' \
                      + '<APIVersion>1.0.0</APIVersion>' \
                      + '<OkUrl>' + kwargs.get("OkUrl") + '</OkUrl>' \
                      + '<FailUrl>' + kwargs.get("FailUrl") + '</FailUrl>' \
                      + '<HashData>' + kwargs.get("HashData") + '</HashData>' \
                      + '<MerchantId>' + kwargs.get("MerchantId") + '</MerchantId>' \
                      + '<CustomerId>' + kwargs.get("CustomerId") + '</CustomerId>' \
                      + '<UserName>' + kwargs.get("UserName") + '</UserName>' \
                      + '<CardNumber>' + kwargs.get("CardNumber") + '</CardNumber>' \
                      + '<CardExpireDateYear>' + kwargs.get("CardExpireDateYear") + '</CardExpireDateYear>' \
                      + '<CardExpireDateMonth>' + kwargs.get("CardExpireDateMonth") + '</CardExpireDateMonth>' \
                      + '<CardCVV2>' + kwargs.get("CardCVV2") + '</CardCVV2>' \
                      + '<CardHolderName>' + kwargs.get("CardHolderName") + '</CardHolderName>' \
                      + '<CardType>' + kwargs.get("CardType") + '</CardType>' \
                      + '<TransactionType>' + kwargs.get("TransactionType") + '</TransactionType>' \
                      + '<InstallmentCount>' + kwargs.get("InstallmentCount") + '</InstallmentCount>' \
                      + '<Amount>' + kwargs.get("Amount") + '</Amount>' \
                      + '<DisplayAmount>' + kwargs.get("DisplayAmount") + '</DisplayAmount>' \
                      + '<CurrencyCode>' + kwargs.get("CurrencyCode") + '</CurrencyCode>' \
                      + '<MerchantOrderId>' + kwargs.get("MerchantOrderId") + '</MerchantOrderId>' \
                      + '<TransactionSecurity>' + kwargs.get("TransactionSecurity") + '</TransactionSecurity>' \
                      + '</KuveytTurkVPosMessage>'
        header = {'Content-Type': 'application/xml'}
        try:
            r = requests.post(kart_onay_url, string_data, header, verify=False)
        except requests.exceptions.ConnectionError as e:
            r = "No response"
        return http.Response(r)

    @http.route([_kuveytturk_callback_url_ok], type='http',
                methods=["GET", "POST"], auth="public", website=False, csrf=False, cors="none")
    def kuveytturk_payment_ok(self, **kwargs):
        provider_obj = self.__get_provider()
        kwargs.update(request.httprequest.data)
        data = unquote(kwargs['AuthenticationResponse'])
        merchant_order_id_start = data.find('<MerchantOrderId>')
        merchant_order_id_stop = data.find('</MerchantOrderId>')
        merchant_order_id = data[merchant_order_id_start + 17:merchant_order_id_stop]
        amount_start = data.find('<Amount>')
        amount_end = data.find('</Amount>')
        amount = data[amount_start + 8:amount_end]
        md_start = data.find('<MD>')
        md_end = data.find('</MD>')
        md = data[md_start + 4:md_end]
        password = provider_obj.kuveytturk_password
        username = provider_obj.kuveytturk_username
        merchant_id = provider_obj.kuveytturk_merchant_id
        customer_id = provider_obj.kuveytturk_customer_id
        if provider_obj.state == "enabled":
            odeme_onay_url = config.SANAL_POS["live_odeme_onay_url"]
        else:
            odeme_onay_url = config.SANAL_POS["test_odeme_onay_url"]
        hashed_password = base64.b64encode(
            hashlib.sha1(password.encode('ISO-8859-9')).digest()).decode()
        hashed_data = base64.b64encode(hashlib.sha1(
            f'{merchant_id}{merchant_order_id}{amount}{username}{hashed_password}'.encode(
                "ISO-8859-9")).digest()).decode()
        xml = f"""
            <KuveytTurkVPosMessage xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <APIVersion>1.0.0</APIVersion>
            <HashData>{hashed_data}</HashData>
            <MerchantId>{merchant_id}</MerchantId>
            <CustomerId>{customer_id}</CustomerId>
            <UserName>{username}</UserName>
            <TransactionType>Sale</TransactionType>
            <InstallmentCount>0</InstallmentCount>
            <Amount>{amount}</Amount>
            <MerchantOrderId>{str(merchant_order_id)}</MerchantOrderId>
            <TransactionSecurity>3</TransactionSecurity>
            <KuveytTurkVPosAdditionalData>
            <AdditionalData>
            <Key>MD</Key>
            <Data>{md}</Data>
            </AdditionalData>
            </KuveytTurkVPosAdditionalData>
            </KuveytTurkVPosMessage>
            """
        headers = {'Content-Type': 'application/xml'}

        r = requests.post(odeme_onay_url, data=xml.encode('ISO-8859-9'), headers=headers)

        text = r.text
        response_code_start = text.find('<ResponseCode>')
        response_code_end = text.find('</ResponseCode>')
        response_code = text[response_code_start + 14:response_code_end]

        response_message_start = text.find('<ResponseMessage>')
        response_message_end = text.find('</ResponseMessage>')
        response_message = text[response_message_start + 17:response_message_end]

        currency_code_start = text.find('<CurrencyCode>')
        currency_code_end = text.find('</CurrencyCode>')
        currency_code = text[currency_code_start + 14:currency_code_end]

        data = dict(
            Amount=amount,
            CurrencyCode=currency_code,
            HashData=hashed_data,
            MerchantOrderId=str(merchant_order_id),
            ResponseCode=response_code,
            ResponseMessage=response_message,
        )

        acquirer_obj = request.env["payment.acquirer"].sudo().search([('provider', '=', 'kuveytturk')])
        res = acquirer_obj.retrive_data(data)
        data.update(res)
        request.env['payment.transaction'].sudo().form_feedback(data, 'kuveytturk')
        if request.httprequest.path == self._kuveytturk_callback_url:
            return http.Response("OK")
        return werkzeug.utils.redirect('/payment/process')

        #return http.Response(r)

    @http.route([_kuveytturk_callback_url_fail], type='http',
                methods=["GET", "POST"], auth="public", website=False, csrf=False, cors="none")
    def kuveytturk_payment_fail(self, **kwargs):
        kwargs.update(request.httprequest.data)
        data = unquote(kwargs['AuthenticationResponse'])

        response_code_start = data.find('<ResponseCode>')
        response_code_end = data.find('</ResponseCode>')
        response_code = data[response_code_start + 14:response_code_end]

        response_message_start = data.find('<ResponseMessage>')
        response_message_end = data.find('</ResponseMessage>')
        response_message = data[response_message_start + 17:response_message_end]

        merchant_order_id_start = data.find('<MerchantOrderId>')
        merchant_order_id_stop = data.find('</MerchantOrderId>')
        merchant_order_id = data[merchant_order_id_start + 17:merchant_order_id_stop]

        data = dict(
            MerchantOrderId=str(merchant_order_id),
            ResponseCode=response_code,
            ResponseMessage=response_message,
        )

        acquirer_obj = request.env["payment.acquirer"].sudo().search([('provider', '=', 'kuveytturk')])
        res = acquirer_obj.retrive_data(data)
        data.update(res)
        request.env['payment.transaction'].sudo().form_feedback(data, 'kuveytturk')
        if request.httprequest.path == self._kuveytturk_callback_url:
            return http.Response("OK")
        return werkzeug.utils.redirect('/payment/process')

        #return http.Response(r)
