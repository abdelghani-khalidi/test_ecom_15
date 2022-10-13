odoo.define('payment_kuveytturk.payment_kuveytturk', function(require){
    "use strict";

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var publicWidget = require('web.public.widget');
    var qweb = core.qweb;
    var _t = core._t;

    if ($.blockUI) {
        $.blockUI.defaults.css.border = '0';
        $.blockUI.defaults.css["background-color"] = '';
        $.blockUI.defaults.overlayCSS["opacity"] = '0.9';
    }

    var KuveytTurkPaymentForm = publicWidget.Widget.extend({
        _initBlockUI: function(message) {
            if ($.blockUI) {
                $.blockUI({
                    'message': '<h2 class="text-white"><img src="/web/static/src/img/spin.png" class="fa-pulse"/>'+'<br />' + message + '</h2>'
                });
            }
            $("#o_payment_form_pay").attr('disabled', 'disabled');
        },
        _revokeBlockUI: function() {
            if ($.blockUI) {$.unblockUI();}
            $("#o_payment_form_pay").removeAttr('disabled');
        },
        _getFormData: function() {
            var data = {}
            this.$form.find('input').each(function() {
                data[$(this).attr('name')] = $(this).val();
            });
            return data
        },
        init: function(){
            this.$form = $('form[provider="kuveytturk"]');
            this.formData = {};
            this.start();
        },
        start: function(){
            var self = this;
            self._initBlockUI(_t("Redirecting to KuveytTurk Payment Gateway..."));
            this.formData = self._getFormData();
            console.log(this.formData);
            if(this.formData.status == "success"){
                self._buildPopup()
            } else {
                self._showErrorMessage(_t('KuveytTurk Error'), this.formData.errorMessage);
            }
        },
        _showErrorMessage: function(title, message) {
            this._revokeBlockUI();
            $("#o_payment_form_pay").hide();
            return new Dialog(null, {
                title: _t('Error: ') + _.str.escapeHTML(title),
                size: 'medium',
                $content: "<p>" + (_.str.escapeHTML(message) || "") + "</p>" ,
                buttons: [
                {text: _t('Ok'), close: true}]}).open();
        },
        _buildPopup: function(){
            var checked_radio = $('input[name="pm_id"]:checked');
            if (checked_radio.attr("data-provider") == "kuveytturk") {
                /*$('#o_payment_form_pay').on('click', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }*/
                this._revokeBlockUI();
                var data = this.formData;
                var KuveytTurkModal = `
<div id="kuveytturk_payment_form_modal" class="modal fade" role="dialog">
    <div class="modal-dialog modal-lg" style="margin-top:100px;">
        <form action="${data.post_url}" method="post" class="payment-form-box" >
            <div class="modal-content">
                <div class="modal-header">
                    <h4 class="modal-title">Pay with KuveytTürk</h4>
                    <button type="button" class="close fa fa-times" data-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <input type="hidden" name="OkUrl" value="${data.OkUrl}" />
                    <input type="hidden" name="FailUrl" value="${data.FailUrl}" />
                    <input type="hidden" name="HashData" value="${data.HashData}" />
                    <input type="hidden" name="MerchantId" value="${data.MerchantId}" />
                    <input type="hidden" name="CustomerId" value="${data.CustomerId}" />
                    <input type="hidden" name="UserName" value="${data.UserName}" />
                    <input type="hidden" name="CardType" value="${data.CardType}" />
                    <input type="hidden" name="TransactionType" value="${data.TransactionType}" />
                    <input type="hidden" name="InstallmentCount" value="${data.InstallmentCount}" />
                    <input type="hidden" name="TransactionType" value="${data.TransactionType}" />
                    <input type="hidden" name="Amount" value="${data.Amount}" />
                    <input type="hidden" name="DisplayAmount" value="${data.DisplayAmount}" />
                    <input type="hidden" name="CurrencyCode" value="${data.CurrencyCode}" />
                    <input type="hidden" name="MerchantOrderId" value="${data.MerchantOrderId}" />
                    <input type="hidden" name="TransactionSecurity" value="${data.TransactionSecurity}" />
                    <div class="row">
                        <div class="col-sm-6">
                            <div class="form-group">
                                <label>Card Holder Name:</label>
                                <input type="text" name="CardHolderName" class="form-control" value="${data.CardHolderName}" />
                            </div>
                            <div class="form-group">
                                <label>Card Number:</label>
                                <input type="text" name="CardNumber_display" class="form-control" value="${data.test_mode == '1'?'4033602562020327':''}" />
                                <input type="hidden" name="CardNumber" class="form-control" value="${data.test_mode == '1'?'4033602562020327':''}" />
                            </div>
                            <div class="row">
                                <div class="form-group col-sm-6">
                                    <label>Month:</label>
                                    <input type="text" name="CardExpireDateMonth" class="form-control" value="${data.test_mode == '1'?'01':''}"  />
                                </div>
                                <div class="form-group col-sm-6">
                                    <label>Year:</label>
                                    <input type="text" name="CardExpireDateYear" class="form-control" value="${data.test_mode == '1'?'30':''}" />
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Security Code:</label>
                                <input type="text" name="CardCVV2" class="form-control" value="${data.test_mode == '1'?'861':''}" />
                            </div>
                        </div>
                        <div class="col-sm-6" style="margin-top:7%;">
                            <div class='card-wrapper'></div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <!--<button type="button" class="btn btn-default" data-dismiss="modal"> Close </button>-->
                    <button type="submit" class="btn btn-primary btn-block submit"><i class="fa fa-credit-card"></i> Pay Now </button>
                </div>
            </div>
        </form>
    </div>
</div>`;
                $(document).ready(function(){
                    "use strict";
                    $('body').on('click', '.submit', function(e) {
                        alert('test1');
                        console.log('test1')
                        /*e.preventDefault();
                        alert('hj');
                        var x = `dfgfg${}hgfh`;
                        var string_data = '<KuveytTurkVPosMessage xmlns:xsi="http://www.w3.org/2001/XMLSchemainstance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">'+
                         '<APIVersion>1.0.0</APIVersion>'+
                         '<OkUrl>http://127.0.0.1:8014/ok-url/</OkUrl>'+
                         '<FailUrl>http://127.0.0.1:8014/fail-url/</FailUrl>'+
                         '<HashData>'+$('input[name="HashData"]').val()+'</HashData>'+
                         '<CustomerId>400235</CustomerId>'+
                        '<UserName>apitest</UserName>'+
                        '<CardNumber>4033602562020327</CardNumber>'+
                        '<CardExpireDateYear>30</CardExpireDateYear>'+
                        '<CardExpireDateMonth>01</CardExpireDateMonth>'+
                        '<CardCVV2>861</CardCVV2>'+
                        '<CardHolderName>test</CardHolderName>'+
                        '<CardType>Troy</CardType>'+
                        '<TransactionType>Sale</TransactionType>'+
                        '<InstallmentCount>0</InstallmentCount>'+
                        '<Amount>500</Amount>'+
                        '<DisplayAmount>500</DisplayAmount>'+
                        '<CurrencyCode>0949</CurrencyCode>'+
                        '<MerchantOrderId>web-odeme</MerchantOrderId>'+
                        '<TransactionSecurity>3</TransactionSecurity>'+
                        '</KuveytTurkVPosMessage>';
                        $.ajax({
                          url: $('form.payment-form-box').attr('action'),
                          method: "POST",
                          data: string_data,
                          dataType: "application/xml"
                        });*/
                    })
                    $('form.payment-form-box').on('click', function (e) {
                        alert('test2');
                        console.log('test2')
                        /*e.preventDefault();
                        alert('hj');
                        var x = `dfgfg${}hgfh`;
                        var string_data = '<KuveytTurkVPosMessage xmlns:xsi="http://www.w3.org/2001/XMLSchemainstance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">'+
                         '<APIVersion>1.0.0</APIVersion>'+
                         '<OkUrl>http://127.0.0.1:8014/ok-url/</OkUrl>'+
                         '<FailUrl>http://127.0.0.1:8014/fail-url/</FailUrl>'+
                         '<HashData>'+$('input[name="HashData"]').val()+'</HashData>'+
                         '<CustomerId>400235</CustomerId>'+
                        '<UserName>apitest</UserName>'+
                        '<CardNumber>4033602562020327</CardNumber>'+
                        '<CardExpireDateYear>30</CardExpireDateYear>'+
                        '<CardExpireDateMonth>01</CardExpireDateMonth>'+
                        '<CardCVV2>861</CardCVV2>'+
                        '<CardHolderName>test</CardHolderName>'+
                        '<CardType>Troy</CardType>'+
                        '<TransactionType>Sale</TransactionType>'+
                        '<InstallmentCount>0</InstallmentCount>'+
                        '<Amount>500</Amount>'+
                        '<DisplayAmount>500</DisplayAmount>'+
                        '<CurrencyCode>0949</CurrencyCode>'+
                        '<MerchantOrderId>web-odeme</MerchantOrderId>'+
                        '<TransactionSecurity>3</TransactionSecurity>'+
                        '</KuveytTurkVPosMessage>';
                        $.ajax({
                          url: $('form.payment-form-box').attr('action'),
                          method: "POST",
                          data: string_data,
                          dataType: "application/xml"
                        });*/
                    }
                    $('form.payment-form-box').card({
                        container: '.card-wrapper',

                        formSelectors: {
                            nameInput: 'input[name="CardHolderName"]',
                            numberInput: 'input[name="CardNumber_display"]',
                            expiryInput: 'input[name="CardExpireDateMonth"], input[name="CardExpireDateYear"]',
                            cvcInput: 'input[name="CardCVV2"]'
                        }
                    });
                    $('form.payment-form-box input[name="CardNumber_display"]').on('keyup paste', function(){
                        $('form.payment-form-box input[name="CardNumber"]').val($(this).val().replace(/\s/g, ''));
                    });
                });
                $(KuveytTurkModal).appendTo('#wrapwrap');
                $("#kuveytturk_payment_form_modal").modal('show');
                $("#kuveytturk_payment_form_modal").on("hidden.bs.modal", function () {
                    $(this).remove();
                    $("#o_payment_form_pay").removeAttr('disabled');
                    $("#o_payment_form_pay .o_loader").remove();
                    window.location.reload();
                });
            }
        }
    });

    new KuveytTurkPaymentForm();
});