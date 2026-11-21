Views.modals.DealStagesModalView = Views.base.ModalView.extend({
    template: '#deal-stages-modal-tmpl',

    mixins: [Mixins.CommonMixin],

    data: function () {
        return {
            modalName: 'dealStages',
            dealStages: []
        };
    },

    activate: function (done) {
        var self = this;

        return $.when(
            $.getJSON(API.dealStages)
        ).then(function (dealStagesData) {
            self.dealStages = dealStagesData;
            done();
        });
    },

    methods: {
        addDealStage: function (e) {
            var self = this,
                $form = $(e.currentTarget),
                $submit = $form.find('.btn'),
                postData = {
                    name: $form.find('input[name=name]').val()
                };

            if (!postData.name) {
                Utils.notify(i18n.gettext('Enter a stage name'), 'error');
                return;
            }

            $submit.toggleBtnLoading(true);

            $.ajax({
                type: 'POST',
                url: API.dealStages,
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);

                self.dealStages.push(response.deal_stage);
                $form.trigger('reset');

                Utils.notify(i18n.gettext('Stage created'), 'success');
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not create the stage'), 'error');
            });
        },

        deleteDealStage: function (dealStage) {
            var self = this;

            $.post(
                API.dealStages + dealStage.id + '/delete/'
            ).done(function (data) {
                self.dealStages.$remove(dealStage);
                Utils.notify(i18n.gettext('Stage deleted'));
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not delete the stage'), 'error');
            });
        }
    }

});
