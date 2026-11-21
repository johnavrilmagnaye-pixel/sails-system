Views.intro.IntroImportStep1View = Vue.extend({
    template: '#intro-import-step1-tmpl',

    data: function () {
        var companyFieldOptins = [
            {value: 'name', text: i18n.gettext('Company name')},
            {value: 'address', text: i18n.gettext('Address')},
            {value: 'website', text: i18n.gettext('Website')},
            {value: 'phone', text: i18n.gettext('Phone')},
            {value: 'email', text: i18n.gettext('Email address')}
        ];

        var personFieldOptions = [
            {value: 'name', text: i18n.gettext('Full name')},
            {value: 'phone', text: i18n.gettext('Phone')},
            {value: 'email', text: i18n.gettext('Email address')}
        ];

        return {
            form: {
                has_header: true,
                merge_contacts: true,
                company_merge_field: 'name',
                person_merge_field: 'name'
            },
            companyFieldOptions: companyFieldOptins,
            personFieldOptions: personFieldOptions,
            showMergeFields: false
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

            if (companyExtraFields) {
                companyExtraFields.forEach(function (extraField) {
                    self.companyFieldOptions.push({value: extraField.codename, text: extraField.name});
                });
            }

            if (personExtraFields) {
                personExtraFields.forEach(function (extraField) {
                    self.personFieldOptions.push({value: extraField.codename, text: extraField.name});
                });
            }

            done();
        });
    },

    methods: {
        onSkip: function (e) {
            var self = this,
                $submit = $(this.$els.submit);

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: API.intro + 'skip_step/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                self.$dispatch('importStep1Completed');
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                self.handleFormErrors(
                    response,
                    i18n.gettext('An error occurred. Please try again or contact support.')
                );
            });
        },
        onSubmit: function (e) {
            var self = this,
                postData = new FormData(),
                $submit = $(this.$els.submit);

            postData.append('file', this.$els.fileInput.files[0]);
            postData.append('has_header', this.form.has_header);
            postData.append('merge_contacts', this.form.merge_contacts);

            if (this.form.merge_contacts) {
                postData.append('company_merge_field', this.form.company_merge_field);
                postData.append('person_merge_field', this.form.person_merge_field);
            }

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: API.contactsImports,
                type: 'POST',
                data: postData,
                processData: false,
                contentType: false
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                Utils.notify(i18n.gettext('File processed'));
                self.$dispatch('importStep1Completed', response);
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Import failed. Please try again or contact support.'), 'error');
            });
        }
    }
});
