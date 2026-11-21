Mixins.BaseGridMixin = {
    computed: {
        emptyTableFixedColumns: function () {
            return 2 + (this.isAdmin() ? 1 : 0);
        },

        /**
         * Returns the number of rendered header columns for an empty table row.
         * Takes into account number of configurable columns and name, edit cells.
         */
        emptyTableColspan: function () {
            var visibleColumns = _.filter(this.columns, function (column) {
                return column.isVisible === true;
            });

            return visibleColumns.length + this.emptyTableFixedColumns;
        }
    },

    methods: {
        sortTable: function (field) {
            if (!field) {
                return;
            }

            if (this.sortField === field) {
                this.sortOrder = this.sortOrder === '-' ? '' : '-';
            } else {
                this.sortField = field;
                this.sortOrder = '-';
            }

            this.fetchData(true);

            Storage.save('sortField', this.sortField);
            Storage.save('sortOrder', this.sortOrder);
        },

        initExtraFieldColumns: function (extraFields, columns) {
            _.each(extraFields, function (extraField) {
                var extraFieldTypes = Const.EXTRA_FIELD_TYPES,
                    extraFieldColumn = _.findWhere(columns, {name: extraField.codename});

                if (!extraFieldColumn) {
                    var isNumber = false,
                        isDate = false,
                        isDatetime = false,
                        isText = false,
                        isPhone = false,
                        isEmail = false;

                    switch (extraField.type) {
                        case extraFieldTypes.NUMBER:
                            isNumber = true;
                            break;
                        case extraFieldTypes.DATE:
                            isDate = true;
                            break;
                        case extraFieldTypes.DATETIME:
                            isDatetime = true;
                            break;
                        case extraFieldTypes.PHONES:
                            isPhone = true;
                            break;
                        case extraFieldTypes.EMAILS:
                            isEmail = true;
                            break;
                        default:
                            isText = true;
                            break;
                    }

                    columns.push({
                        name: extraField.codename,
                        label: extraField.name,
                        sortFieldName: extraField.codename,
                        isVisible: true,
                        isNumber: isNumber,
                        isDate: isDate,
                        isDatetime: isDatetime,
                        isText: isText,
                        isPhone: isPhone,
                        isEmail: isEmail
                    });
                } else {
                    extraFieldColumn.label = extraField.name;
                }
            });
        }
    }
};
