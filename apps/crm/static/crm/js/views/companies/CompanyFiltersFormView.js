Views.companies.CompanyFiltersFormView = Views.common.FiltersFormView.extend({
    props: ['filters', 'extraFields'],
    data: function () {
        var data = {};

        var form = {
            misc: {
                name: 'misc',
                label: i18n.gettext('Companies'),
                editor: 'select-editor',
                options: [
                    {id: '', text: ''},
                    {id: 'with_deals', text: i18n.gettext('With open deals')},
                    {id: 'without_deals', text: i18n.gettext('No open deals')},
                    {id: 'with_tasks', text: i18n.gettext('With active tasks')},
                    {id: 'without_tasks', text: i18n.gettext('No active tasks')},
                    {id: 'duplicates', text: i18n.gettext('With the same name')}
                ],
                allowClear: true,
                defaultValue: '',
                value: Storage.fetchProperty('filters', 'misc', ''),
                error: ''
            }
        };

        this.initFilterExtraFields(form, this.extraFields);
        this.initFilterCommonFields(form);

        data.form = form;

        return data;
    }

});
