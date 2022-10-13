

class KuveytTurkSaveCardWrapper(object):

    def __init__(self, merchant_id, merchant_username, merchant_password):
        self.merchant_id = merchant_id
        self.merchant_username = merchant_username
        self.merchant_password = merchant_password

    def capi_delete(self):
        pass

    def capi_list(self):
        pass

    def capi_payment_new_card(self):
        pass

    def capi_payment_stored_card(self):
        pass