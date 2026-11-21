Views.modals.DealCurrenciesModalView = Views.base.ModalView.extend({
    template: '#deal-currencies-modal-tmpl',

    mixins: [Mixins.CommonMixin],

    data: function () {
        return {
            modalName: 'dealCurrencies',
            dealCurrencies: [],
            newDealCurrency: null
        };
    },

    activate: function (done) {
        var self = this;

        return $.when(
            $.getJSON(API.dealCurrencies)
        ).then(function (dealCurrenciesData) {
            self.dealCurrencies = dealCurrenciesData;
            done();
        });
    },

    methods: {
        addDealCurrency: function (e) {
            var self = this,
                $form = $(e.currentTarget),
                $submit = $form.find('.btn'),
                postData = {
                    deal_currency_id: parseInt($form.find('select[name=name]').val())
                };

            if (!postData.deal_currency_id) {
                Utils.notify(i18n.gettext('Select a new currency'), 'error');
                return;
            }

            $submit.toggleBtnLoading(true);

            $.ajax({
                type: 'POST',
                url: API.dealCurrencies,
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);

                self.dealCurrencies.push(response.deal_currency);
                self.newDealCurrency = '';

                Utils.notify(i18n.gettext('Currency added'), 'success');
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not create the currency'), 'error');
            });
        },

        deleteDealCurrency: function (dealCurrency) {
            var self = this;

            $.post(
                API.dealCurrencies + dealCurrency.id + '/delete/'
            ).done(function (response) {
                self.dealCurrencies.$remove(dealCurrency);
                Utils.notify(i18n.gettext('Currency deleted'));
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not delete the currency'), 'error');
            });
        }
    }

});
