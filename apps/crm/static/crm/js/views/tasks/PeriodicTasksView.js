Views.tasks.PeriodicTasksView = Vue.extend({
    template: '#periodic-tasks-tmpl',
    replace: true,

    mixins: [
        Mixins.CommonMixin, Mixins.ModalsMixin, Mixins.FetchDataMixin, Mixins.BaseGridMixin
    ],
    computed: {
        emptyTableFixedColumns: function () {
            return 3;
        }
    },
    components: {
        gridPagination: Views.base.GridPaginationView,
        periodicTaskFormModal: Views.modals.PeriodicTaskFormModalView,
        gridConfigModal: Views.modals.GridConfigModalView
    },

    props: ['filters', 'extraFields'],
    data: function () {
        var extraFieldTypes = Const.EXTRA_FIELD_TYPES,
            columnsStorageKey = 'periodicColumns',
            columns = Storage.fetch(columnsStorageKey);

        if (!columns) {
            columns = this.getBaseColumns();
        }

        // _.each(this.extraFields, function (extraField) {
        //     if (!_.findWhere(columns, {name: extraField.codename})) {
        //         var isNumber = false,
        //             isDate = false,
        //             isDatetime = false,
        //             isText = false;
        //
        //         switch (extraField.type) {
        //             case extraFieldTypes.NUMBER:
        //                 isNumber = true;
        //                 break;
        //             case extraFieldTypes.DATE:
        //                 isDate = true;
        //                 break;
        //             case extraFieldTypes.DATETIME:
        //                 isDatetime = true;
        //                 break;
        //             default:
        //                 isText = true;
        //                 break;
        //         }
        //
        //         columns.push({
        //             name: extraField.codename,
        //             label: extraField.name,
        //             sortFieldName: extraField.codename,
        //             isVisible: true,
        //             isNumber: isNumber,
        //             isDate: isDate,
        //             isDatetime: isDatetime,
        //             isText: isText
        //         });
        //     }
        // });

        return {
            itemsApiUrl: API.periodicTasks,
            modelName: 'task',
            items: [],
            sortField: Storage.fetch('sortField', 'created_at'),
            sortOrder: Storage.fetch('sortOrder', '-'),
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
                periodicTaskForm: {
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
        togglePeriodicTaskFormModal: function (showModal, instance) {
            this.modals.periodicTaskForm.show = showModal;
            this.modals.periodicTaskForm.data.instance = instance || null;
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
                    name: 'time',
                    label: i18n.gettext('Time'),
                    sortFieldName: 'time',
                    isVisible: true
                },
                {
                    name: 'period',
                    label: i18n.gettext('Repeat'),
                    sortFieldName: 'period',
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
                }
            ]
        },
        deleteItem: function (itemId) {
            var self = this;

            bootbox.dialog({
                message: i18n.gettext('Are you sure you want to delete this recurring task?'),
                buttons: {
                    cansel: {
                        label: i18n.gettext('Cancel'),
                        className: 'btn-default'
                    },
                    danger: {
                        label: '<i class="fa fa-trash-o"></i> ' + i18n.gettext('Delete'),
                        className: 'btn-danger',
                        callback: function () {
                            $.ajax({
                                type: 'POST',
                                url: self.itemsApiUrl + itemId + '/delete/'
                            }).done(function () {
                                self.fetchData();
                            });
                        }
                    }
                }
            });
        }
    },

    events: {
        periodicTaskSaved: function () {
            this.togglePeriodicTaskFormModal(false);
            this.fetchData();
        }
    }
});
