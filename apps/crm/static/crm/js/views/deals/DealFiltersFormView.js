Views.deals.DealFiltersFormView = Views.common.FiltersFormView.extend({
    props: ['filters', 'extraFields', 'itemsView'],
    data: function () {
        var data = {};

        var form = {
            status: {
                name: 'status',
                label: i18n.gettext('Status'),
                editor: 'select-editor',
                options: [
                    {id: '', text: i18n.gettext('All deals')},
                    {id: '1', text: i18n.gettext('Open')},
                    {id: '2', text: i18n.gettext('Closed')}
                ],
                allowClear: true,
                hidden: this.itemsView !== 'grid',
                defaultValue: '1',
                value: Storage.fetchProperty('filters', 'status', '1'),
                error: ''
            },
            stage: {
                name: 'stage',
                label: i18n.gettext('Stage'),
                editor: 'select-editor',
                options: _.union([{id: '', text: ''}], Storage.fetchProperty('filtersOptions', 'stage', [])),
                allowClear: true,
                optionType: 'deal_stage',
                hidden: this.itemsView !== 'grid',
                defaultValue: '',
                value: Storage.fetchProperty('filters', 'stage', ''),
                error: ''
            },
            budget: {
                name: 'budget',
                label: i18n.gettext('Budget'),
                editor: 'number-range-editor',
                defaultValue: '',
                value: Storage.fetchProperty('filters', 'budget', ''),
                error: ''
            },
            currency: {
                name: 'currency',
                label: i18n.gettext('Currency'),
                editor: 'select-editor',
                options: _.union([{id: '', text: ''}], Storage.fetchProperty('filtersOptions', 'currency', [])),
                allowClear: true,
                optionType: 'deal_currency',
                defaultValue: '',
                value: Storage.fetchProperty('filters', 'currency', ''),
                error: ''
            }
        };

        if (!!form.budget.value) {
            form.budget.valueStart = form.budget.value.split(' - ')[0];
            form.budget.valueEnd = form.budget.value.split(' - ')[1];
        } else {
            form.budget.valueStart = '';
            form.budget.valueEnd = '';
        }

        this.initFilterExtraFields(form, this.extraFields);
        this.initFilterCommonFields(form);

        if (this.isGta()) {
            delete form.budget;
            delete form.currency;
            delete form.user;
            delete form.created_at;
            delete form.tags;
        }

        data.form = form;

        return data;
    },

    activate: function (done) {
        var self = this;

        return $.when(
            $.getJSON(API.dealStages),
            $.getJSON(API.dealCurrencies)
        ).then(function (dealStagesData, dealCurrencyData) {
            self.form.stage.options = _.union(self.form.stage.options, dealStagesData[0]);
            if (!self.isGta()) {
                self.form.currency.options = _.union(self.form.currency.options, dealCurrencyData[0]);
            }

            done();
        });
    },

    watch: {
        itemsView: function (value) {
            this.form.status.hidden = value !== 'grid';
            this.form.stage.hidden = value !== 'grid';
        }
    }

});
