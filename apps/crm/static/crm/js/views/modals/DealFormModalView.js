Views.modals.DealFormModalView = Views.base.ModalView.extend({
    template: '#deal-form-modal-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.FormMixin],
    components: {
        textEditor: Views.editors.TextEditor,
        textAreaEditor: Views.editors.TextAreaEditor,
        selectEditor: Views.editors.SelectEditor,
        dateEditor: Views.editors.DateEditor,
        dateTimeEditor: Views.editors.DateTimeEditor
    },

    props: ['modalData'], // extraFields, instance, initialCompany, initialPerson
    data: function () {
        var data = this.modalData;

        data.modalName = 'dealForm';

        var form = {
            name: {
                name: 'name',
                label: i18n.gettext('Name'),
                editor: 'text-editor',
                value: '',
                error: ''
            },
            company: {
                name: 'company',
                label: i18n.gettext('Company'),
                placeholder: i18n.gettext('Select a company'),
                editor: 'select-editor',
                optionType: 'company',
                options: !!data.initialCompany ? [{id: data.initialCompany.id, text: data.initialCompany.name}] : [],
                allowClear: true,
                minInput: 2,
                value: !!data.initialCompany ? data.initialCompany.id : '',
                error: ''
            },
            person: {
                name: 'person',
                label: i18n.gettext('Person'),
                placeholder: i18n.gettext('Select a contact'),
                editor: 'select-editor',
                optionType: 'person',
                options: !!data.initialPerson ? [{id: data.initialPerson.id, text: data.initialPerson.name}] : [],
                queryParams: {},
                allowClear: true,
                minInput: 2,
                value: !!data.initialPerson ? data.initialPerson.id : '',
                error: ''
            },
            budget: {
                name: 'budget',
                label: i18n.gettext('Budget'),
                editor: 'text-editor',
                inputType: 'number',
                value: 0,
                error: ''
            },
            currency: {
                name: 'currency',
                label: i18n.gettext('Currency'),
                editor: 'select-editor',
                options: [],
                value: '',
                error: ''
            },
            status: {
                name: 'status',
                label: i18n.gettext('Status'),
                editor: 'select-editor',
                options: [
                    {id: 1, text: i18n.gettext('In progress')},
                    {id: 2, text: i18n.gettext('Successfully completed')},
                    {id: 3, text: i18n.gettext('Lost')}
                ],
                value: 1,
                error: ''
            },
            stage: {
                name: 'stage',
                label: i18n.gettext('Stage'),
                editor: 'select-editor',
                options: [],
                value: '',
                error: ''
            }
        };

        this.initExtraFields(form, data.extraFields);

        form = _.extend(form, {
            tags: {
                name: 'tags',
                label: i18n.gettext('Tags'),
                placeholder: i18n.gettext('Select tags'),
                editor: 'select-editor',
                optionType: 'tag',
                multiple: true,
                tags: true,
                value: '',
                error: ''
            },
            responsibles: {
                name: 'responsibles',
                label: i18n.gettext('Assignees'),
                placeholder: i18n.gettext('Select assignees'),
                editor: 'select-editor',
                multiple: true,
                optionType: 'user',
                value: '',
                error: ''
            },
            details: {
                name: 'details',
                label: i18n.gettext('Deal description'),
                editor: 'text-area-editor',
                cols: 40,
                rows: 10,
                value: '',
                error: ''
            }
        });

        data.isEdit = false;
        if (!!data.instance) {
            data.isEdit = true;
            this.setInstanceValues(form, data.instance);
        }

        if (this.isGta()) {
            delete form.tags;
        }

        data.form = form;

        return data;
    },

    activate: function (done) {
        var self = this;

        return $.when(
            $.getJSON(API.dealCurrencies),
            $.getJSON(API.dealStages)
        ).then(function (dealCurrencyData, dealStageData) {
            var currencyValue = self.form.currency.value,
                stageValue = self.form.stage.value;

            self.form.currency.options = dealCurrencyData[0];
            self.form.stage.options = dealStageData[0];

            if (self.isEdit) {
                self.form.currency.value = parseInt(currencyValue);
                self.form.stage.value = parseInt(stageValue);
            } else {
                if (!!self.form.currency.options.length) {
                    self.form.currency.value = self.form.currency.options[0].id
                }

                if (!!self.form.stage.options.length) {
                    self.form.stage.value = self.form.stage.options[0].id
                }
            }

            done();
        });
    },

    ready: function () {
        this.$watch('form.company.value', function (value) {
           if (!!this.form.person) {
                this.form.person.queryParams.company = value;

                if (!value) {
                    this.form.person.value = '';
                }
            }
        });
    },

    methods: {
        doRequest: function (action) {
            var self = this,
                $submit = $(this.$els.submit),
                postData = this.getFormData(),
                url = API.deals + (!!self.instance ? self.instance.id + '/edit/' : 'add/');

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: url,
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                Utils.notify(self.isEdit ? i18n.gettext('Changes saved'): i18n.gettext('New deal added'));
                self.$dispatch('dealSaved', action, response.deal);
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                self.handleFormErrors(
                    response,
                    i18n.gettext('Could not save the deal. Please try again or contact support.')
                );
            });
        },

        submit: function () {
            this.doRequest();
        },

        submitAndAddMore: function () {
            this.doRequest('addMore');
        },

        submitAndGoTo: function () {
            this.doRequest('goTo');
        }
    }
});
