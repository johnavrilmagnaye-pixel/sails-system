Views.tasks.TaskCardLayoutView = Views.base.CardView.extend({
    LAST_ITEM_ID_KEY: 'task_last_item_id',
    CARD_TAB_KEY: 'task_card_tab',

    template: '#task-card-layout-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.ModalsMixin],
    components: {
        taskFormModal: Views.modals.TaskFormModalView,
        cardNotes: Views.common.CardNotesView,
        cardUploads: Views.common.CardUploadsView,
        cardExtraFields: Views.common.CardExtraFieldsView
    },

    data: function () {
        return {
            itemId: this.$route.params.id,
            itemUrl: this.$route.path,
            itemsApiUrl: API.tasks,
            item: {},
            notes: [],
            uploads: [],
            extraFields: [],
            modelName: 'task',
            redirectUrl: Urls.tasks,
            modelGenitive: i18n.gettext('task'),
            cardTab: this.getLastItemId() === this.$route.params.id.toString() ? this.getCardTab() : 'notes',
            modals: {
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
                };

            return $.when(
                $.getJSON(this.itemsApiUrl + this.itemId + '/'),
                $.getJSON(API.notes, queryParams),
                $.getJSON(API.uploads, queryParams),
                $.getJSON(API.extraFields, {content_type__model: this.modelName})
            ).then(function (itemData, notesData, uploadsData, extraFieldsData) {
                self.item = itemData[0];
                self.notes = notesData[0];
                self.uploads = uploadsData[0];
                self.extraFields = extraFieldsData[0];
            }).fail(function (jqXHR) {
                if (jqXHR.status === 404) {
                    router.go(self.redirectUrl);
                }
            });
        }
    },

    methods: {
        completeTask: function (e) {
            var self = this,
                $btn = $(e.currentTarget);

            $btn.toggleBtnLoading(true);

            $.ajax({
                url: this.itemsApiUrl + this.itemId + '/complete/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $btn.toggleBtnLoading(false);
                Utils.notify(i18n.gettext('Task completed'));
                self.notes.unshift(response.note);
                self.item = response.task;
            }).fail(function (response) {
                $btn.toggleBtnLoading(false);
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not complete the task'), 'error');
            });
        },
        undoneTask: function (e) {
            var self = this,
                $btn = $(e.currentTarget);

            $btn.toggleBtnLoading(true);

            $.ajax({
                url: this.itemsApiUrl + this.itemId + '/undone/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $btn.toggleBtnLoading(false);
                Utils.notify(i18n.gettext('Task reopened'));
                self.notes.unshift(response.note);
                self.item = response.task;
            }).fail(function (response) {
                $btn.toggleBtnLoading(false);
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not reopen the task'), 'error');
            });
        },
        toggleTaskFormModal: function (showModal) {
            this.modals.taskForm.show = showModal;
            this.modals.taskForm.data.instance = this.item;
            this.modals.taskForm.data.extraFields = this.extraFields;
        }
    },

    events: {
        taskSaved: function (action, data) {
            this.toggleTaskFormModal(false);
            this.item = data.task;
        }
    }
});
