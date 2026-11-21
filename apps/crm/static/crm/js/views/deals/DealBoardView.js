Views.deals.DealBoardView = Vue.extend({
    template: '#deal-board-tmpl',
    replace: true,

    mixins: [Mixins.CommonMixin, Mixins.ModalsMixin, Mixins.FetchDataMixin],
    components: {
        dealFormModal: Views.modals.DealFormModalView
    },

    props: ['filters', 'extraFields'],
    data: function () {
        return {
            itemsApiUrl: API.dealsBoard,
            modelName: 'deal',
            modelPlural: i18n.gettext('deal'),
            modelGenitive: i18n.gettext('deal'),
            boardData: {},
            modals: {
                dealForm: {
                    show: false,
                    data: {
                        instance: null,
                        extraFields: this.extraFields
                    }
                }
            }

        }
    },

    computed: {
        noDeals: function () {
            return _.flatten(
                _.pluck(_.values(this.boardData), 'deals')
            ).length === 0;
        }
    },

    activate: function (done) {
        var self = this,
            itemsParams = this.getFetchDataParams();

        $.when(
            $.getJSON(API.dealsBoard, itemsParams)
        ).then(function (itemsData) {
            self.setFetchDataResponse(itemsData);
            done();
        });
    },

    methods: {
        getFetchDataParams: function () {
            return _.pick(this.filters, _.identity);
        },
        setFetchDataResponse: function (data) {
            this.boardData = data;
        },
        deleteItem: function (deal) {
            var self = this;

            bootbox.dialog({
                message: i18n.gettext('Are you sure you want to delete ') + self.modelGenitive + '?',
                buttons: {
                    cansel: {
                        label: i18n.gettext('Cancel'),
                        className: 'btn-default'
                    },
                    danger: {
                        label: '<i class="fa fa-trash-o"></i> ' + i18n.gettext('Delete'),
                        className: 'btn-danger',
                        callback: function () {
                            $.post(deal.url + 'delete/').done(function (data) {
                                if (data['success']) {
                                    self.boardData[deal.stage.id].deals.$remove(deal);
                                }
                            });
                        }
                    }
                }
            });
        },
        completeStage: function (deal) {
            var self = this;

            $.ajax({
                url: API.deals + deal.id + '/complete_stage/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                self.boardData[deal.stage.id].deals.$remove(deal);

                if (response.deal.status === Const.DEAL_STATUSES.COMPLETED) {
                    Utils.notify(i18n.gettext('Stage <b>') +  deal.stage.name + i18n.gettext('</b> completed. The deal was completed successfully.'));
                    return;
                }

                self.boardData[response.deal.stage.id].deals.push(response .deal);
                Utils.notify(i18n.gettext('Stage <b>') +  deal.stage.name + i18n.gettext('</b> completed'));
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not complete the stage'), 'error');
            });
        },
        failStage: function (deal) {
            var self = this;

            $.ajax({
                url: API.deals + deal.id + '/fail_stage/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                self.boardData[deal.stage.id].deals.$remove(deal);
                Utils.notify(i18n.gettext('Deal lost at stage <b>') + deal.stage.name + '</b>.');
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not complete the stage'), 'error');
            });
        },
        toggleDealFormModal: function (showModal, instance) {
            this.modals.dealForm.show = showModal;
            this.modals.dealForm.data.instance = instance || null;
        }
    },

    events: {
        dealSaved: function (action, deal) {
            var self = this;

            this.toggleDealFormModal(false);

            switch (action) {
                case 'addMore':
                    this.fetchData();
                    setTimeout(function () {
                        self.toggleDealFormModal(true);
                    }, 300);
                    break;
                case 'goTo':
                    this.$router.go(deal.url);
                    break;
                default:
                    this.fetchData();
            }
        }
    }
});
