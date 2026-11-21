Views.persons.PersonGridView = Vue.extend({
    template: '#person-grid-tmpl',
    replace: true,

    mixins: [
        Mixins.CommonMixin, Mixins.ModalsMixin, Mixins.FetchDataMixin, Mixins.BaseGridMixin, Mixins.GridCheckboxesMixin
    ],
    components: {
        gridPagination: Views.base.GridPaginationView,
        importStep1Modal: Views.modals.ImportContactsStep1ModalView,
        importStep2Modal: Views.modals.ImportContactsStep2ModalView,
        responsiblesModal: Views.modals.ResponsiblesModalView,
        tagsModal: Views.modals.TagsModalView,
        personFormModal: Views.modals.PersonFormModalView,
        companyFormModal: Views.modals.CompanyFormModalView,
        gridConfigModal: Views.modals.GridConfigModalView
    },

    props: ['filters', 'personExtraFields', 'companyExtraFields'],
    data: function () {
        var self = this,
            extraFieldTypes = Const.EXTRA_FIELD_TYPES;

        var columns = Storage.fetch('columns');

        if (!columns) {
            columns = this.getBaseColumns();
        }

        // removing contact type column
        _.remove(columns, function(column) {
            return column.name === 'type';
        });

        this.initExtraFieldColumns(this.extraFields, columns);

        return {
            itemsApiUrl: API.persons,
            deleteItemsUrl: API.personsBatchDelete,
            modelName: 'person',
            modelPlural: i18n.gettext('contacts'),
            items: [],
            sortField: Storage.fetch('sortField', 'created_at'),
            sortOrder: Storage.fetch('sortOrder', '-'),
            checkedAll: false,
            columns: columns,
            paginationData: {
                page: 1,
                pageSize: Storage.fetch('pageSize', 25),
                count: null,
                previous: null,
                next: null
            },
            modals: {
                importStep1: {
                    show: false
                },
                importStep2: {
                    show: false,
                    data: {}
                },
                responsibles: {
                    show: false,
                    data: {
                      baseUrl: API.persons,
                      targetLabel: i18n.gettext('contacts'),
                      isGrid: true,
                      query: {},
                      itemIds: [],
                      filteredCnt: null,
                    }
                },
                tags: {
                    show: false,
                    data: {
                      baseUrl: API.persons,
                      targetLabel: i18n.gettext('contacts'),
                      isGrid: true,
                      query: {},
                      itemIds: [],
                      filteredCnt: null,
                    }
                },
                personForm: {
                    show: false,
                    data: {
                        instance: null,
                        extraFields: this.personExtraFields
                    }
                },
                companyForm: {
                    show: false,
                    data: {
                        extraFields: this.companyExtraFields,
                        isQuickForm: true
                    }
                },
                gridConfig: {
                    show: false,
                    data: {
                        columns: null,
                        isPerson: true
                    }
                }
            },
            contactsImportId: null
        };
    },

    activate: function (done) {
        var self = this,
            queryParams = this.getFetchDataParams();

        return $.when(
            $.getJSON(this.itemsApiUrl, queryParams)
        ).then(function (itemsData) {
            self.setFetchDataResponse(itemsData);
            done();
        });
    },

    methods: {
        checkContactsImport: function () {
            var self = this;

            $.getJSON(
                API.contactsImports + this.contactsImportId + '/'
            ).done(function (response) {
                if (response.is_completed) {
                    Utils.notify(response.msg || i18n.gettext('Contact import completed successfully'), 'success', 10000);
                    self.fetchData(true);
                    return;
                }

                setTimeout(self.checkContactsImport, 10000);
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Import error'), 'error');
            });
        },
        toggleImportStep1Modal: function (showModal) {
            this.modals.importStep1.show = showModal;
        },
        toggleImportStep2Modal: function (showModal) {
            this.modals.importStep2.show = showModal;
        },
        toggleResponsiblesModal: function (showModal) {
            if (showModal) {
              this.modals.responsibles.data.query = _.pick(this.filters, _.identity);
              this.modals.responsibles.data.itemIds = this.getCheckedItems(this.items);
              this.modals.responsibles.data.filteredCnt = this.paginationData.count;
            }

            this.modals.responsibles.show = showModal;
        },
        toggleTagsModal: function (showModal) {
            if (showModal) {
              this.modals.tags.data.query = _.pick(this.filters, _.identity);
              this.modals.tags.data.itemIds = this.getCheckedItems(this.items);
              this.modals.tags.data.filteredCnt = this.paginationData.count;
            }

            this.modals.tags.show = showModal;
        },
        togglePersonFormModal: function (showModal, instance) {
            this.modals.personForm.show = showModal;
            this.modals.personForm.data.instance = instance || null;
        },
        toggleCompanyFormModal: function (showModal) {
            this.modals.companyForm.show = showModal;
        },
        toggleGridConfigModal: function (showModal) {
            this.modals.gridConfig.data.columns = this.columns;
            this.modals.gridConfig.show = showModal;
        },
        getBaseColumns: function () {
            return [
                {
                    name: 'company',
                    label: i18n.gettext('Company'),
                    sortFieldName: 'company__name',
                    isVisible: true
                },
                {
                    name: 'post',
                    label: i18n.gettext('Job title'),
                    sortFieldName: ' post',
                    isVisible: true
                },
                {
                    name: 'phone',
                    label: i18n.gettext('Phone'),
                    isVisible: true
                },
                {
                    name: 'email',
                    label: i18n.gettext('Email address'),
                    isVisible: true
                },
                {
                    name: 'tags',
                    label: i18n.gettext('Tags'),
                    isVisible: false
                },
                {
                    name: 'responsibles',
                    label: i18n.gettext('Assignees'),
                    isVisible: false
                },
                {
                    name: 'details',
                    label: i18n.gettext('Additional information'),
                    sortFieldName: 'details',
                    isVisible: false
                },
                {
                    name: 'user',
                    label: i18n.gettext('Created by'),
                    sortFieldName: 'user',
                    isVisible: false
                },
                {
                    name: 'created_at',
                    label: i18n.gettext('Date created'),
                    sortFieldName: 'created_at',
                    isVisible: false
                }
            ]
        }
    },

    events: {
        importStep1Completed: function (response) {
            this.modals.importStep2.data = response;
            this.toggleImportStep1Modal(false);
            this.toggleImportStep2Modal(true);
        },
        importStep2Completed: function (contactsImportId) {
            this.toggleImportStep2Modal(false);
            this.contactsImportId = contactsImportId;
            setTimeout(this.checkContactsImport, 10000);
        },
        welcomeStartImport: function () {
            this.toggleImportStep1Modal(true);
        },
        personSaved: function (action, person) {
            var self = this;
            this.togglePersonFormModal(false);

            switch (action) {
                case 'addMore':
                    this.fetchData();
                    setTimeout(function () {
                        self.togglePersonFormModal(true);
                    }, 300);
                    break;
                case 'goTo':
                    this.$router.go(person.url);
                    break;
                default:
                    this.fetchData();
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
