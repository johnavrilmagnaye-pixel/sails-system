Views.tasks.TaskFiltersFormView = Views.common.FiltersFormView.extend({
    props: ['filters', 'extraFields', 'itemsView'],
    data: function () {
        var data = {};

        var form = {
            state: {
                name: 'state',
                label: i18n.gettext('Status'),
                editor: 'select-editor',
                allowClear: true,
                options: [
                    {id: '', text: i18n.gettext('All tasks')},
                    {id: '1', text: i18n.gettext('Current')},
                    {id: '2', text: i18n.gettext('Completed')},
                    {id: '3', text: i18n.gettext('Overdue')}
                ],
                defaultValue: '1',
                value: Storage.fetchProperty('filters', 'state', '1'),
                error: ''
            },
            expire_date: {
                name: 'expire_date',
                label: i18n.gettext('Due date'),
                editor: 'date-range-editor',
                allowClear: true,
                hidden: this.itemsView !== 'grid',
                defaultValue: '',
                value: Storage.fetchProperty('filters', 'expire_date', ''),
                error: ''
            }
        };

        this.initFilterExtraFields(form, this.extraFields);
        this.initFilterCommonFields(form);

        if (this.isGta()) {
            _.remove(form.state.options, {
                id: '3'
            });
        }

        data.form = form;

        return data;
    },

    watch: {
        itemsView: function (value) {
            this.form.expire_date.hidden = value === 'calendar';
        }
    }
});
