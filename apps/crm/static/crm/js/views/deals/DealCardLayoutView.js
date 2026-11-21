Views.deals.DealCardLayoutView = Views.base.CardView.extend({
    LAST_ITEM_ID_KEY: 'deal_last_item_id',
    CARD_TAB_KEY: 'deal_card_tab',

    template: '#deal-card-layout-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.ModalsMixin],
    components: {
        dealFormModal: Views.modals.DealFormModalView,
        taskFormModal: Views.modals.TaskFormModalView,
        cardTasks: Views.common.CardTasksView,
        cardNotes: Views.common.CardNotesView,
        cardUploads: Views.common.CardUploadsView,
        cardExtraFields: Views.common.CardExtraFieldsView
    },

    data: function () {
        return {
            itemId: this.$route.params.id,
            itemUrl: this.$route.path,
            itemsApiUrl: API.deals,
            item: {},
            notes: [],
            uploads: [],
            tasks: [],
            dealStages: [],
            dealExtraFields: [],
            taskExtraFields: [],
            extraFieldTypes: Const.EXTRA_FIELD_TYPES,
            modelName: 'deal',
            redirectUrl: Urls.deals,
            modelGenitive: i18n.gettext('deal'),
            cardTab: this.getLastItemId() === this.$route.params.id.toString() ? this.getCardTab() : 'notes',
            modals: {
                dealForm: {
                    show: false,
                    data: {
                        instance: null,
                        extraFields: []
                    }
                },
                taskForm: {
                    show: false,
                    data: {
                        instance: null,
                        extraFields: []
                    }
                }
            }
        }
    },

    route: {
        data: function (transition) {
            var self = this,
                queryParams = {
                    content_type__model: this.modelName,
                    item_id: this.itemId
                },
                dealParams = {
                    deal: this.itemId
                };

            return $.when(
                $.getJSON(API.deals + this.itemId + '/'),
                $.getJSON(API.notes, queryParams),
                $.getJSON(API.uploads, queryParams),
                $.getJSON(API.tasks, dealParams),
                $.getJSON(API.dealStages),
                $.getJSON(API.extraFields)
            ).then(function (itemData, notesData, uploadsData, tasksData, dealStagesData, extraFieldsData) {
                self.item = itemData[0];

                self.notes = notesData[0];
                self.uploads = uploadsData[0];
                self.tasks = tasksData[0];

                self.dealStages = dealStagesData[0];

                self.dealExtraFields = _.filter(extraFieldsData[0], function (extraField) { return extraField.content_type === 'deal'});
                self.taskExtraFields = _.filter(extraFieldsData[0], function (extraField) { return extraField.content_type === 'task'});
            }).fail(function (jqXHR) {
                if (jqXHR.status === 404) {
                    router.go(self.redirectUrl);
                }
            });
        }
    },

    methods: {
        completeStage: function () {
            var self = this;

            $.ajax({
                url: API.deals + this.itemId + '/complete_stage/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                self.notes.unshift(response.note);
                self.item = response.deal;
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not complete the stage'), 'error');
            });

        },
        failStage: function () {
            var self = this;

            $.ajax({
                url: API.deals + this.itemId + '/fail_stage/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                self.notes.unshift(response.note);
                self.item = response.deal;
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not complete the stage'), 'error');
            });
        },
        toggleDealFormModal: function (showModal) {
            this.modals.dealForm.data.instance = this.item;
            this.modals.dealForm.data.extraFields = this.dealExtraFields;
            this.modals.dealForm.show = showModal;
        },
        toggleTaskFormModal: function (showModal) {
            this.modals.taskForm.data.initialCompany = this.item.company;
            this.modals.taskForm.data.initialPerson = this.item.person;
            this.modals.taskForm.data.initialDeal = this.item;
            this.modals.taskForm.data.extraFields = this.taskExtraFields;
            this.modals.taskForm.show = showModal;
        }
    },

    events: {
        dealSaved: function (action, deal) {
            this.toggleDealFormModal(false);
            this.item = deal;
        },
        taskSaved: function (action, data) {
            var self = this;

            setTimeout(function () {
                self.tasks.unshift(data.task);
            }, 400);

            this.toggleTaskFormModal(false);

            switch (action) {
                case 'addMore':
                    setTimeout(function () {
                        self.toggleTaskFormModal(true);
                    }, 300);
                    break;
                case 'goTo':
                    this.$router.go(data.task.url);
                    break;
            }
        }
    }
});
