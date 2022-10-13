import base64
import hashlib
import pprint
from collections.abc import Iterable
from logging import getLogger

from werkzeug import urls

from odoo import models, fields, api, _
from odoo.addons.payment.controllers.portal import PaymentPortal
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from odoo.tools.float_utils import float_compare
from ..controllers.main import PaymentKuveytTurkController

# Supported Currencies: TRY
CURRENCY_CODES = {
    "TL": "0949",
    "TRY": "0949",
}

_logger = getLogger(__name__)


def _add_tx_to_current_session(tx):
    # TODO: Due to cookie default SameSite policy change in 2020, Odoo loses session id, and forgets about the sale.
    #  We remember him the transactions to "watch".
    sale_id = tx.env["sale.order"].search([("name", "=", tx.reference.split("-", 1)[0])]).id
    PaymentPortal.add_payment_transaction(tx)
    request.session["__website_sale_last_tx_id"] = tx.id
    request.session["sale_order_id"] = sale_id
    request.session["sale_last_order_id"] = sale_id


class PaymentKuveytTurk(models.Model):
    _inherit = 'payment.acquirer'
    _description = 'KuveytTurk Payment Acquirer'

    provider = fields.Selection(selection_add=[('kuveytturk', _('KuveytTurk'))], ondelete={"kuveytturk": "set default"})
    kuveytturk_customer_id = fields.Char(string="Customer ID", default="400235")
    kuveytturk_merchant_id = fields.Char(string="Merchant ID", default="496")
    kuveytturk_username = fields.Char(string="Username", default="apitest")
    kuveytturk_password = fields.Char(string="Password", default="api123")
    kuveytturk_max_installment = fields.Integer(string="Max Installment", default=0)
    kuveytturk_callback_base_url = fields.Char(string="Callback Base URL", required_if_provider="kuveytturk",
                                               groups='base.group_user')
    kuveytturk_use_callback_base_url = fields.Boolean(string="Use Callback Base URL", groups='base.group_user')
    kuveytturk_use_samesite_workaround = fields.Boolean(string="Use SameSite Workaround", groups="base.group_user")

    def _generate_kuveytturk_request_dict(self, values) -> dict:
        currency = values.get("currency").name

        CardHolderName = f"{values.get('billing_partner_first_name')} {values.get('billing_partner_last_name')}"
        test_mode = "1" if self.state == "test" else "0"

        amount = float(values.get("amount"))
        amount = amount * 100
        amount = "{:.0f}".format(amount)
        payment_amount = amount
        merchant_oid = values.get('reference')
        if not currency in CURRENCY_CODES.keys():
            raise ValidationError(_("Your currency is not supported by the KuveytTurk payment system."))

        # payment_amount = 2.700,5
        password = self.kuveytturk_password
        user_name = self.kuveytturk_username
        merchant_id = self.kuveytturk_merchant_id
        if self.kuveytturk_use_callback_base_url:
            base_url = self.kuveytturk_callback_base_url
        else:
            base_url = self.get_base_url()
        ok_url = urls.url_join(base_url, PaymentKuveytTurkController._kuveytturk_callback_url_ok)
        fail_url = urls.url_join(base_url, PaymentKuveytTurkController._kuveytturk_callback_url_fail)

        hashed_password = base64.b64encode(
            hashlib.sha1(f"{password}".encode('ISO-8859-9')).digest()).decode()
        hashed_data = base64.b64encode(hashlib.sha1(
            f"{merchant_id}{merchant_oid}{payment_amount}{ok_url}{fail_url}{user_name}{hashed_password}".encode(
                'ISO-8859-9')).digest()).decode()

        data = {
            "OkUrl": ok_url,
            "FailUrl": fail_url,
            "HashData": hashed_data,
            "MerchantId": merchant_id,
            "CustomerId": f"{self.kuveytturk_customer_id}",
            "UserName": user_name,
            "CardHolderName": CardHolderName,
            "CardType": "Troy",
            "TransactionType": "Sale",
            "InstallmentCount": f"{self.kuveytturk_max_installment}",
            "Amount": payment_amount,
            "DisplayAmount": payment_amount,
            "CurrencyCode": CURRENCY_CODES[currency],
            "MerchantOrderId": merchant_oid,
            "TransactionSecurity": "3",
            "test_mode": test_mode,
            "status": "success",
        }
        return data

    def kuveytturk_form_generate_values(self, values: dict) -> dict:
        values['amount'] = round(values['amount'], 2)
        values.update(self._generate_kuveytturk_request_dict(values=values))
        timeout_date = fields.Datetime.add(fields.Datetime.now(), minutes=-300)
        transactions = self.env["payment.transaction"].search([("acquirer_id", "=", self.id),
                                                               ("state", "=", "draft"),
                                                               ("create_date", "<", timeout_date)])
        if transactions:
            _logger.info(f"Removing timeout transactions: {transactions}")
            for transaction in transactions:
                transaction.state_message = _("Payment timeout")
                transaction._set_transaction_cancel()

        return values

    def retrive_data(self, data: dict) -> dict:
        try:
            data.update({'locale': self._context.get("lang").split('_')[0]})

            time_out_date = fields.Datetime.add(fields.Datetime.now(), minutes=-5)
            transactions = self.env["payment.transaction"].search([("reference", "=", data["MerchantOrderId"]),
                                                                   ("state", "=", "draft")])
            for transaction in transactions:
                if data["ResponseCode"] == "00":
                    transaction._set_transaction_done()
                else:
                    transaction._set_transaction_error(
                        msg=data.get("ResponseMessage", _("The payment has been canceled")))
        except Exception as e:
            raise UserError(e)
        return data

    @api.model
    def _create_missing_journal_for_acquirers(self, company=None):
        acquirer_modules = self.env['ir.module.module'].search(
            [('name', 'like', 'payment_%'), ('state', 'in', ('to install', 'installed'))])
        acquirer_names = [a.name.split('_')[-1] for a in acquirer_modules]

        company = company or self.env.company
        acquirers = self.env['payment.acquirer'].search(
            [('provider', 'in', acquirer_names), ('journal_id', '=', False), ('company_id', '=', company.id)])

        journals = self.env['account.journal']
        for acquirer in acquirers.filtered(lambda l: not l.journal_id and l.company_id.chart_template_id):
            acquirer.journal_id = self.env['account.journal'].create(
                acquirer._prepare_account_journal_vals())
            journals += acquirer.journal_id
        return journals


class TrasanctionKuveytTurkPayment(models.Model):
    _inherit = 'payment.transaction'

    kuveytturk_tx_resp = fields.Char(string="Transaction Response", groups='base.group_user')

    @api.model
    def _kuveytturk_form_get_tx_from_data(self, data):
        reference = data.get("MerchantOrderId")
        if not reference:
            raise ValidationError(_("KuveytTurk system didn't send a Merchant OID!"))

        _logger.error(msg=f"reference: {reference}")
        tx = self.search([("reference", "=", reference)])
        _logger.error(msg=f"tx: {tx}")
        if not tx or len(tx) > 1:
            err = _('received data for reference %s') % (
                pprint.pformat(reference))
            if not tx:
                err += _("; No order found!")
            else:
                err += _("; Found multiple orders!")

            _logger.error(err)
        tx = tx[0] if tx and isinstance(tx, Iterable) else tx
        # TODO: Why don't tx'es have times by default?
        if not tx.date:
            tx.date = fields.Datetime.now()

        if tx.acquirer_id.kuveytturk_use_samesite_workaround:
            _add_tx_to_current_session(tx)
        return tx

    def _kuveytturk_form_get_invalid_parameters(self, data):
        invalid_params = []
        amount: float = float(data.get("Amount", "0.00"))
        amount = amount * 0.01
        currency: str = "0" + data.get("CurrencyCode", "")
        expected_currency = CURRENCY_CODES.get(self.currency_id.name, "")

        # Check for amount billed and acquired from bank.
        if float_compare(amount, self.amount, 2) != 0:
            invalid_params.append(('amount', amount, f"{self.amount: .2f}"))
        if not expected_currency or currency != expected_currency:
            invalid_params.append(('currency', currency, expected_currency))
        return invalid_params

    def _kuveytturk_form_validate(self, data):
        status = data.get("ResponseCode")
        res = {
            'date': fields.datetime.now(),
            'acquirer_reference': data.get("MerchantOrderId"),
            'state_message': data.get('ResponseMessage')
        }
        self.write(res)
        if status == '00':
            self._set_transaction_done()
            self.execute_callback()
            _logger.info('Validated KuveytTurk payment for tx %s: set as done' % (self.reference))
            return True
        else:
            error = data.get('ResponseMessage')
            _logger.error(error)
            self._set_transaction_error(error)
            return False
