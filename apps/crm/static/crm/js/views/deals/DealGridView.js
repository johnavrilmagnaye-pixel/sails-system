Views.deals.DealGridView = Vue.extend({
    template: '#deal-grid-tmpl',
    replace: true,

    mixins: [
        Mixins.CommonMixin, Mixins.ModalsMixin, Mixins.FetchDataMixin, Mixins.BaseGridMixin, Mixins.GridCheckboxesMixin
    ],
    components: {
        gridPagination: Views.base.GridPaginationView,
        responsiblesModal: Views.modals.ResponsiblesModalView,
        tagsModal: Views.modals.TagsModalView,
        dealFormModal: Views.modals.DealFormModalView,
        gridConfigModal: Views.modals.GridConfigModalView
    },

    props: ['filters', 'extraFields'],
    data: function () {
        var extraFieldTypes = Const.EXTRA_FIELD_TYPES,
            columns = Storage.fetch('columns');

        if (!columns) {
            columns = this.getBaseColumns();
        }

        this.initExtraFieldColumns(this.extraFields, columns);

        return {
            itemsApiUrl: API.deals,
            deleteItemsUrl: API.dealsBatchDelete,
            modelName: 'deal',
            modelPlural: i18n.gettext('deal'),
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
                responsibles: {
                    show: false,
                    data: {
                      baseUrl: API.deals,
                      targetLabel: i18n.gettext('deals'),
                      isGrid: true,
                      query: {},
                      itemIds: [],
                      filteredCnt: null,
                    }
                },
                tags: {
                    show: false,
                    data: {
                      baseUrl: API.deals,
                      targetLabel: i18n.gettext('deals'),
                      isGrid: true,
                      query: {},
                      itemIds: [],
                      filteredCnt: null,
                    }
                },
                dealForm: {
                    show: false,
                    data: {
                        instance: null,
                        extraFields: this.extraFields
                    }
                },
                gridConfig: {
                    show: false,
                    data: {
                        columns: null
                    }
                }
            }
        }
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
        toggleDealFormModal: function (showModal, instance) {
            this.modals.dealForm.show = showModal;
            this.modals.dealForm.data.instance = instance || null;
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
                    name: 'person',
                    label: i18n.gettext('Person'),
                    sortFieldName: 'person__name',
                    isVisible: true
                },
                {
                    name: 'budget',
                    label: i18n.gettext('Budget'),
                    sortFieldName: 'budget',
                    isVisible: true
                },
                {
                    name: 'status',
                    label: i18n.gettext('Status'),
                    sortFieldName: 'status',
                    isVisible: true
                },
                {
                    name: 'stage',
                    label: i18n.gettext('Stage'),
                    sortFieldName: 'stage',
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
                    label: i18n.gettext('Deal description'),
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
