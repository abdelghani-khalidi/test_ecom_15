from logging import getLogger

_logger = getLogger(__name__)

SANAL_POS = {
    'customer_id': '400235',
    'merchant_id': '496',
    'username': 'apitest',
    'password': 'api123',
    'max_installment': '0',
    'test_kart_onay_url': 'https://boatest.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelPayGate',
    'test_odeme_onay_url': 'https://boatest.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelProvisionGate',
    'live_kart_onay_url': 'https://boa.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelPayGate',
    'live_odeme_onay_url': 'https://boa.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelProvisionGate',
}
