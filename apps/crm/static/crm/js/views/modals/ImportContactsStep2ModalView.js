Views.modals.ImportContactsStep2ModalView = Views.base.ModalView.extend({
    template: '#import-contacts-step2-modal-tmpl',

    mixins: [Mixins.CommonMixin],

    props: ['importData'],
    data: function () {
        var fieldsRange = _.range(_.keys(this.importData.fields_map).length),
            origCompanyFieldOptions = [
                {value: 'company_name', text: i18n.gettext('Company name')},
                {value: 'address', text: i18n.gettext('Address')},
                {value: 'website', text: i18n.gettext('Website')},
                {value: 'company_responsibles', text: i18n.gettext('Assignees')},
                {value: 'company_tags', text: i18n.gettext('Tags')}
            ],
            origPersonFieldOptions = [
                {value: 'person_name', text: i18n.gettext('Full name')},
                {value: 'post', text: i18n.gettext('Job title')},
                {value: 'person_responsibles', text: i18n.gettext('Assignees')},
                {value: 'person_tags', text: i18n.gettext('Tags')}
            ],
            origCommonFieldOptions = [
                {value: 'phones', text: i18n.gettext('Phone')},
                {value: 'emails', text: i18n.gettext('Email address')},
                {value: 'details', text: i18n.gettext('Additional information')}
            ];

        return {
            modalName: 'importStep2',
            form: {
                name: '',
                contentType: 'company',
                error: ''
            },
            contentTypeOptions: [
                {value: 'company', text: i18n.gettext('companies')},
                {value: 'person', text: i18n.gettext('contacts')},
                {value: 'common', text: i18n.gettext('companies and contacts')}
            ],

            rowsCnt: this.importData.rows_cnt,
            fieldsMap: this.importData.fields_map,
            headerRow: this.importData.header_row,
            sampleRows: this.importData.sample_rows,
            contactsImportId: this.importData.contacts_import_id,
            duplicatesCnt: this.importData.duplicates_cnt,

            fieldsRange: fieldsRange,
            companyFieldOptions: origCompanyFieldOptions,
            personFieldOptions: origPersonFieldOptions,
            commonFieldOptions: origCommonFieldOptions
        }
    },

    activate: function (done) {
        var self = this,
            companyQueryParams = {content_type__model: 'company'},
            personQueryParams = {content_type__model: 'person'};

        return $.when(
            $.getJSON(API.extraFields, companyQueryParams),
            $.getJSON(API.extraFields, personQueryParams)
        ).then(function (companyExtraFieldsData, personExtraFieldsData) {
            var companyExtraFields = companyExtraFieldsData[0],
                personExtraFields = personExtraFieldsData[0];

            if (companyExtraFields.length) {
                companyExtraFields.forEach(function (field) {
                    var p = _.findWhere(personExtraFields, {name: field.name});

                    if (p) {
                        self.commonFieldOptions.push({
                            value: field.codename, text: field.name
                        });
                        _.remove(personExtraFields, p);
                    } else {
                        self.companyFieldOptions.push({
                            value: field.codename, text: field.name
                        });
                    }
                });
            }

            if (personExtraFields.length) {
                personExtraFields.forEach(function (field) {
                    self.personFieldOptions.push({
                        value: field.codename, text: field.name
                    });
                });
            }

            done();
        });
    },

    ready: function () {
        this.$watch('fieldsMap', this.onFieldsMapChange, {
            deep: true,
            immediate: true
        });
    },

    methods: {
        toggleExtraFieldForm: function () {
            $(this.$els.extraFieldForm).toggleClass('hidden');
        },
        addExtraField: function (e) {
            if (this.form.name.length > 200) {
                this.form.error = i18n.gettext('Name is too long')
            } else {
                this.form.error = ''
            }

            var self = this,
                postData = {
                    name: this.form.name
                },
                $form = $(e.currentTarget),
                $submit = $form.find('button[type="submit"]');

            $submit.toggleBtnLoading(true);

            if (this.form.contentType === 'company') {
                $.post(
                    '/extra_fields/company/add/',
                    postData
                ).done(function (response) {
                    $submit.toggleBtnLoading(false);

                    if (response['success']) {
                        self.companyFieldOptions.push({
                            value: response.extra_field.codename, text: response.extra_field.name
                        });
                        self.form.name = '';
                        self.form.error = '';
                        Utils.notify(i18n.gettext('New field added'));
                    } else {
                        self.form.error = response.errors.name[0];
                    }
                });
            } else if (this.form.contentType === 'person') {
                $.post(
                    '/extra_fields/person/add/',
                    postData
                ).done(function (response) {
                    $submit.toggleBtnLoading(false);

                    if (response['success']) {
                        self.personFieldOptions.push({
                            value: response.extra_field.codename, text: response.extra_field.name
                        });
                        self.form.name = '';
                        self.form.error = '';
                        Utils.notify(i18n.gettext('New field added'));
                    } else {
                        self.form.error = response.errors.name[0];
                    }
                });
            } else {
                $.post(
                    '/extra_fields/company/add/',
                    postData
                ).done(function (response) {
                    $submit.toggleBtnLoading(false);

                    if (response['success']) {
                        $.post(
                            '/extra_fields/person/add/',
                            postData
                        ).done(function (response) {
                            $submit.toggleBtnLoading(false);

                            if (response['success']) {
                                self.commonFieldOptions.push({
                                    value: response.extra_field.codename, text: response.extra_field.name
                                });
                                self.form.name = '';
                                self.form.error = '';
                                Utils.notify(i18n.gettext('New field added'));
                            } else {
                                self.form.error = response.errors.name[0];
                            }
                        });
                    } else {
                        self.form.error = response.errors.name[0];
                    }
                });
            }
        },
        onFieldsMapChange: function () {
            var selectedFields = _.values(this.fieldsMap),
                $fieldsTable = $(this.$els.fieldsTable);

            $fieldsTable.find('option').prop('disabled', false);

            _.forEach(selectedFields, function (val) {
                $fieldsTable.find('option[value="' + val + '"]').prop('disabled', true);
            });
        },
        onSubmit: function (e) {
            var self = this,
                postData = {
                    fields_map: this.fieldsMap
                },
                selectedFields = _.values(this.fieldsMap),
                $submit = $(e.currentTarget);

            if (selectedFields.indexOf('company_name') === -1 && selectedFields.indexOf('person_name') === -1) {
                Utils.notify(
                    i18n.gettext('None of the required fields is selected. Please specify which column in the file ') +
                    i18n.gettext('matches the company name or contact full name.'),
                    'error'
                );
                return;
            }

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: API.contactsImports + this.contactsImportId + '/start_import/',
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                Utils.notify(i18n.gettext('Contact import started. You will receive a notification when it is complete.'));
                self.$dispatch('importStep2Completed', self.contactsImportId);
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Import error'), 'error');
            });
        }
    }
});
