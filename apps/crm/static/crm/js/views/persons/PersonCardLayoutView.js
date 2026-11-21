Views.persons.PersonCardLayoutView = Views.base.CardView.extend({
    LAST_ITEM_ID_KEY: 'person_last_item_id',
    CARD_TAB_KEY: 'person_card_tab',

    template: '#person-card-layout-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.ModalsMixin],
    components: {
        companyFormModal: Views.modals.CompanyFormModalView,
        personFormModal: Views.modals.PersonFormModalView,
        dealFormModal: Views.modals.DealFormModalView,
        taskFormModal: Views.modals.TaskFormModalView,
        cardDeals: Views.common.CardDealsView,
        cardTasks: Views.common.CardTasksView,
        cardNotes: Views.common.CardNotesView,
        cardUploads: Views.common.CardUploadsView,
        cardExtraFields: Views.common.CardExtraFieldsView
    },

    data: function () {
        return {
            itemId: this.$route.params.id,
            itemUrl: this.$route.path,
            itemsApiUrl: API.persons,
            item: {},
            notes: [],
            uploads: [],
            deals: [],
            tasks: [],
            companyExtraFields: [],
            personExtraFields: [],
            dealExtraFields: [],
            taskExtraFields: [],
            modelName: 'person',
            redirectUrl: Urls.persons,
            modelGenitive: i18n.gettext('contact'),
            cardTab: this.getLastItemId() === this.$route.params.id.toString() ? this.getCardTab() : 'notes',
            modals: {
                companyForm: {
                    show: false,
                    data: {
                        extraFields: [],
                        isQuickForm: true
                    }
                },
                personForm: {
                    show: false,
                    data: {
                        instance: null,
                        extraFields: []
                    }
                },
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
                personParams = {
                    person: this.itemId
                };

            return $.when(
                $.getJSON(this.itemsApiUrl + this.itemId + '/'),
                $.getJSON(API.notes, queryParams),
                $.getJSON(API.uploads, queryParams),
                $.getJSON(API.tasks, personParams),
                $.getJSON(API.deals, personParams),
                $.getJSON(API.extraFields)
            ).then(function (itemData, notesData, uploadsData, tasksData, dealsData, extraFieldsData) {
                self.item = itemData[0];

                self.notes = notesData[0];
                self.uploads = uploadsData[0];
                self.tasks = tasksData[0];
                self.deals = dealsData[0];

                self.companyExtraFields = _.filter(extraFieldsData[0], {content_type: 'company'});
                self.personExtraFields = _.filter(extraFieldsData[0], {content_type: 'person'});
                self.dealExtraFields = _.filter(extraFieldsData[0], {content_type: 'deal'});
                self.taskExtraFields = _.filter(extraFieldsData[0], {content_type: 'task'});
            }).fail(function (jqXHR) {
                if (jqXHR.status === 404) {
                    router.go(self.redirectUrl);
                }
            });
        }
    },

    methods: {
        toggleCompanyFormModal: function (showModal) {
            this.modals.companyForm.data.extraFields = this.companyExtraFields;
            this.modals.companyForm.show = showModal;
        },
        togglePersonFormModal: function (showModal) {
            this.modals.personForm.data.instance = this.item;
            this.modals.personForm.data.extraFields = this.personExtraFields;
            this.modals.personForm.show = showModal;
        },
        toggleDealFormModal: function (showModal) {
            this.modals.dealForm.data.extraFields = this.dealExtraFields;
            this.modals.dealForm.data.initialCompany = this.item.company;
            this.modals.dealForm.data.initialPerson = this.item;
            this.modals.dealForm.show = showModal;
        },
        toggleTaskFormModal: function (showModal) {
            this.modals.taskForm.data.initialCompany = this.item.company;
            this.modals.taskForm.data.initialPerson = this.item;
            this.modals.taskForm.data.extraFields = this.taskExtraFields;
            this.modals.taskForm.show = showModal;
        }
    },

    events: {
        personSaved: function (action, person) {
            this.togglePersonFormModal(false);
            this.item = person;
        },
        dealSaved: function (action, deal) {
            var self = this;

            setTimeout(function () {
                self.deals.unshift(deal);
            }, 400);

            this.toggleDealFormModal(false);

            switch (action) {
                case 'addMore':
                    setTimeout(function () {
                        self.toggleDealFormModal(true);
                    }, 300);
                    break;
                case 'goTo':
                    this.$router.go(deal.url);
                    break;
            }
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
        },
        companySaved: function (action, company) {
            this.toggleCompanyFormModal(false);
            this.$broadcast('companyAdded', company);
        },
        addCompany: function () {
            this.toggleCompanyFormModal(true);
        }
    }
});
