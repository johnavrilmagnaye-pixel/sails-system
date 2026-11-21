Views.modals.ResponsiblesModalView = Views.base.ModalView.extend({
    template: '#responsibles-modal-tmpl',

    mixins: [Mixins.CommonMixin],

    props: ['modalData'],  // modalData: baseUrl, targetLabel, isGrid, query, itemIds, filteredCnt
    data: function () {
        var data = this.modalData;

        data.modalName = 'responsibles';
        data.form = {
            responsibles: [],
            action: 'add'
        };

        return data;
    },

    methods: {
        doRequest: function(postData) {
            var self = this,
                $submit = $(this.$els.submit);

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: this.modalData.baseUrl + 'batch_edit_responsibles/',
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                Utils.notify(i18n.gettext('Assignees updated'));
                self.cancelModal();
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not update assignees'), 'error');
            });
        },
        onSubmit: function () {
            this.doRequest(this.form)
        },
        save: function(onlySelected) {
            var postData = this.form;

            postData.query = this.modalData.query;
            if (!!onlySelected) {
                postData.item_ids = this.modalData.itemIds;
            }

            this.doRequest(postData);
        }
    }
});
