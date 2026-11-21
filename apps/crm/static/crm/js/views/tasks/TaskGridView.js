Views.tasks.TaskGridView = Vue.extend({
    template: '#task-grid-tmpl',
    replace: true,

    mixins: [
        Mixins.CommonMixin, Mixins.ModalsMixin, Mixins.FetchDataMixin, Mixins.BaseGridMixin, Mixins.GridCheckboxesMixin
    ],
    components: {
        gridPagination: Views.base.GridPaginationView,
        responsiblesModal: Views.modals.ResponsiblesModalView,
        tagsModal: Views.modals.TagsModalView,
        taskFormModal: Views.modals.TaskFormModalView,
        gridConfigModal: Views.modals.GridConfigModalView
    },

    props: ['filters', 'extraFields'],
    data: function () {
        var columnsStorageKey = 'columns',
            columns = Storage.fetch(columnsStorageKey);

        if (!columns) {
            columns = this.getBaseColumns();
        }

        this.initExtraFieldColumns(this.extraFields, columns);

        return {
            itemsApiUrl: API.tasks,
            deleteItemsUrl: API.tasksBatchDelete,
            modelName: 'task',
            modelPlural: i18n.gettext('task'),
            items: [],
            sortField: Storage.fetch('sortField', 'created_at'),
            sortOrder: Storage.fetch('sortOrder', '-'),
            checkedAll: false,
            columnsStorageKey: columnsStorageKey,
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
                      baseUrl: API.tasks,
                      targetLabel: i18n.gettext('tasks'),
                      isGrid: true,
                      query: {},
                      itemIds: [],
                      filteredCnt: null,
                    }
                },
                tags: {
                    show: false,
                    data: {
                      baseUrl: API.tasks,
                      targetLabel: i18n.gettext('tasks'),
                      isGrid: true,
                      query: {},
                      itemIds: [],
                      filteredCnt: null,
                    }
                },
                taskForm: {
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
        toggleTaskFormModal: function (showModal, instance) {
            this.modals.taskForm.show = showModal;
            this.modals.taskForm.data.instance = instance || null;
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
                    name: 'deal',
                    label: i18n.gettext('Deal'),
                    sortFieldName: 'deal__name',
                    isVisible: true
                },
                {
                    name: 'expire_date',
                    label: i18n.gettext('Due date'),
                    sortFieldName: 'expire_date',
                    isVisible: true
                },
                {
                    name: 'state',
                    label: i18n.gettext('Status'),
                    sortFieldName: 'state',
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
                    label: i18n.gettext('Task description'),
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
        taskSaved: function (action, data) {
            var self = this;

            this.toggleTaskFormModal(false);

            switch (action) {
                case 'addMore':
                    this.fetchData();
                    setTimeout(function () {
                        self.toggleTaskFormModal(true);
                    }, 300);
                    break;
                case 'goTo':
                    this.$router.go(data.task.url);
                    break;
                default:
                    this.fetchData();
            }
        }
    }
});
